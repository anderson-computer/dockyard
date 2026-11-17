"""Management authentication and input boundaries; boot clients only see boot routes."""
import hmac
import ipaddress
import json
import os
import re
import secrets
import threading
import time
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit
from flask import abort, jsonify, redirect, render_template, request, session
from werkzeug.security import check_password_hash

LEAF = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$')

def safe_leaf(value, suffix=None):
    if not isinstance(value, str) or not LEAF.fullmatch(value) or '..' in value or (suffix and not value.lower().endswith(suffix)):
        raise ValueError('Invalid resource name; use letters, numbers, underscore, hyphen and single dots')
    return value

def confined(directory, leaf):
    safe_leaf(leaf)
    base = Path(directory).resolve()
    target = (base / leaf).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError('Resource points outside its storage directory') from None
    return target

def single_line(value, maximum=2048):
    if not isinstance(value, str) or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise ValueError('Expected single-line text')
    return value

def validate_menu(menu):
    if not isinstance(menu, dict) or not isinstance(menu.get('entries', []), list) or len(menu.get('entries', [])) > 500:
        raise ValueError('Invalid boot menu')
    single_line(menu.get('title', 'Dockyard Boot Menu'), 128)
    try:
        timeout = int(menu.get('timeout', 60))
        if not 0 <= timeout <= 3600:
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('Menu timeout must be 0-3600 seconds') from None
    seen = set()
    for entry in menu.get('entries', []):
        if not isinstance(entry, dict):
            raise ValueError('Invalid menu entry')
        ident = safe_leaf(entry.get('id'))
        if ident in ('menu', 'shell', 'reboot', 'exit'):
            raise ValueError('Boot entry ID is reserved for menu navigation')
        if ident in seen:
            raise ValueError('Duplicate boot entry ID')
        seen.add(ident)
        safe_leaf(entry.get('iso_id', ident))
        single_line(entry.get('label', ident), 256)
        single_line(entry.get('kernel_args', ''))
        if entry.get('kickstart'):
            safe_leaf(entry['kickstart'])
        if entry.get('os_type', 'rhel') not in ('rhel', 'ubuntu', 'debian', 'other'):
            raise ValueError('Unsupported OS type')
    if menu.get('default'):
        safe_leaf(menu['default'])
    menu['timeout'] = timeout
    return menu

def validate_settings(settings):
    if not isinstance(settings, dict):
        raise ValueError('Invalid settings')
    allowed = {'server_ip','web_port','boot_port','dhcp_enabled','dhcp_interface','dhcp_start','dhcp_end','dhcp_netmask','dhcp_gateway','dhcp_dns','dhcp_lease_time','version'}
    if set(settings) - allowed:
        raise ValueError('Unknown settings fields; authentication is configured by the server administrator')
    if 'dhcp_enabled' in settings and not isinstance(settings['dhcp_enabled'], bool):
        raise ValueError('DHCP enabled must be true or false')
    for field in ('server_ip','dhcp_start','dhcp_end','dhcp_netmask','dhcp_gateway','dhcp_dns'):
        if settings.get(field):
            ipaddress.IPv4Address(settings[field])
    for field in ('web_port','boot_port'):
        if field in settings and (isinstance(settings[field], bool) or not 1 <= int(settings[field]) <= 65535):
            raise ValueError('Invalid port')
    if settings.get('dhcp_interface') and not re.fullmatch(r'[A-Za-z0-9_.:-]{1,32}', settings['dhcp_interface']):
        raise ValueError('Invalid network interface')
    if settings.get('dhcp_lease_time', '12h') not in ('1h','4h','8h','12h','24h','48h'):
        raise ValueError('Invalid DHCP lease time')
    return settings

def install_security(app):
    config_dir = Path(os.environ.get('DOCKYARD_CONFIG', '/etc/dockyard'))
    key = os.environ.get('DOCKYARD_SECRET_KEY')
    if not key:
        key = (config_dir / 'session.key').read_text().strip()
    if len(key) < 32:
        raise RuntimeError('Persistent session key is missing or invalid')
    app.secret_key = key
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict', SESSION_COOKIE_SECURE=os.environ.get('DOCKYARD_HTTPS') == 'true', PERMANENT_SESSION_LIFETIME=timedelta(minutes=30))
    attempts, lock = {}, threading.Lock()

    def csrf_token():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        return session['csrf']

    app.jinja_env.globals['csrf_token'] = csrf_token

    @app.before_request
    def protect_management():
        public = request.path in ('/menu.ipxe','/healthz','/help','/about') or request.path.startswith('/static/')
        if request.path == '/login' and (request.content_length or 0) > 16384:
            abort(413, 'Login request too large')
        if session.get('username') and not public:
            auth_path = config_dir / 'auth.json'
            current = json.loads(auth_path.read_text()) if auth_path.exists() else {}
            if session.get('auth_revision') != current.get('auth_revision', 'initial'):
                session.clear()
        if not public and request.path != '/login' and not session.get('username'):
            return (jsonify(error='Authentication required'), 401) if request.path.startswith('/api/') else redirect('/login')
        if request.method not in ('GET','HEAD','OPTIONS'):
            origin = request.headers.get('Origin')
            if origin and urlsplit(origin).netloc != request.host:
                abort(403, 'Cross-origin request rejected')
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token', '')
            if not hmac.compare_digest(str(token), str(session.get('csrf') or secrets.token_urlsafe(32))):
                abort(403, 'Invalid request token; refresh the page')

    @app.route('/login', methods=['GET','POST'])
    def login():
        error = None
        if request.method == 'POST':
            username, password = request.form.get('username',''), request.form.get('password','')
            if len(username) > 128 or len(password) > 4096 or not password:
                abort(400)
            peer, now = request.remote_addr, time.time()
            with lock:
                if len(attempts) > 4096:
                    attempts.clear()
                recent = [t for t in attempts.get(peer, []) if now - t < 60]
                if len(recent) >= 10:
                    abort(429, 'Too many sign-in attempts; wait one minute')
                attempts[peer] = recent + [now]
            auth_path = config_dir / 'auth.json'
            settings = json.loads(auth_path.read_text()) if auth_path.exists() else {}
            accepted = username == settings.get('username', 'admin') and bool(settings.get('password_hash')) and check_password_hash(settings['password_hash'], password)
            if not accepted and settings.get('ldap_enabled'):
                from auth import create_auth_from_settings
                handler = create_auth_from_settings(settings)
                accepted = bool(handler and handler.authenticate_admin(username, password))
            if accepted:
                session.clear()
                session['username'] = username
                session['auth_revision'] = settings.get('auth_revision', 'initial')
                session['csrf'] = secrets.token_urlsafe(32)
                session.permanent = True
                return redirect('/')
            error = 'Invalid credentials or directory access denied'
        return render_template('login.html', error=error)

    @app.post('/logout')
    def logout():
        session.clear()
        return redirect('/login')

    @app.get('/healthz')
    def health():
        return jsonify(application='Dockyard', version='1.0.0', status='ok')

    @app.get('/help')
    def help_page():
        return render_template('help.html')

    @app.get('/about')
    def about_page():
        return render_template('about.html')
