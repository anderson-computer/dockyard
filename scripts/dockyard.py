"""Root-reviewed configuration and service commands for Dockyard."""
import argparse
import getpass
import ipaddress
import json
import os
import pwd
import shutil
import subprocess
import sys
import tempfile
import secrets
from pathlib import Path
sys.path.insert(0, '/opt/dockyard/web')
from security import validate_menu, validate_settings, safe_leaf
from werkzeug.security import generate_password_hash

DATA = Path('/var/lib/dockyard')
CONFIG = Path('/etc/dockyard')

def root():
    if os.geteuid():
        raise SystemExit('Run this operation with sudo.')

def write_json(path, data, mode=0o600, owner='dockyard'):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as out:
            json.dump(data, out, indent=2)
        os.chmod(temporary, mode)
        account = pwd.getpwnam(owner)
        os.chown(temporary, account.pw_uid, account.pw_gid if owner != 'root' else pwd.getpwnam('dockyard').pw_gid)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

def network(args):
    root()
    ip = ipaddress.IPv4Address(args.server_ip)
    if not Path('/sys/class/net', safe_leaf(args.interface)).exists():
        raise SystemExit('Network interface does not exist on this server.')
    settings = dict(server_ip=str(ip), boot_port=8081, web_port=8080, dhcp_enabled=bool(args.dhcp_start), dhcp_interface=args.interface, dhcp_lease_time='12h')
    lines = ['# Dockyard dedicated configuration', 'port=0', 'bind-interfaces', 'interface='+args.interface, 'except-interface=lo', 'enable-tftp', 'tftp-root=/var/lib/dockyard/tftp', 'log-dhcp', 'dhcp-match=set:ipxe,175', 'dhcp-userclass=set:ipxe,iPXE', 'dhcp-match=set:efi-x86_64,option:client-arch,7', 'dhcp-match=set:efi-x86_64,option:client-arch,9']
    if args.dhcp_start:
        if not all((args.dhcp_end, args.netmask, args.gateway, args.dns)):
            raise SystemExit('DHCP requires start/end, netmask, gateway and DNS. Omit DHCP arguments for TFTP-only operation.')
        network = ipaddress.IPv4Network(str(ip)+'/'+args.netmask, strict=False)
        first, last = ipaddress.IPv4Address(args.dhcp_start), ipaddress.IPv4Address(args.dhcp_end)
        if first not in network or last not in network or first > last or first <= ip <= last:
            raise SystemExit('Invalid DHCP pool or pool includes the server IP.')
        for value in (args.gateway, args.dns):
            ipaddress.IPv4Address(value)
        settings.update(dhcp_start=str(first), dhcp_end=str(last), dhcp_netmask=args.netmask, dhcp_gateway=args.gateway, dhcp_dns=args.dns)
        lines += [f'dhcp-range={first},{last},{args.netmask},12h', 'dhcp-option=option:router,'+args.gateway, 'dhcp-option=option:dns-server,'+args.dns, 'dhcp-leasefile=/var/lib/dockyard/network/dnsmasq.leases']
    lines += [f'dhcp-boot=tag:ipxe,http://{ip}:8081/menu.ipxe',f'dhcp-boot=tag:efi-x86_64,tag:!ipxe,ipxe/ipxe.efi,pxeserver,{ip}',f'dhcp-boot=tag:!efi-x86_64,tag:!ipxe,ipxe/undionly.kpxe,pxeserver,{ip}']
    validate_settings(settings)
    config_file = CONFIG / 'dnsmasq.conf'
    temporary = CONFIG / 'dnsmasq.conf.pending'
    temporary.write_text('\n'.join(lines)+'\n')
    subprocess.run(['/usr/sbin/dnsmasq','--test','--conf-file='+str(temporary)], check=True)
    os.replace(temporary, config_file)
    write_json(DATA/'config/settings.json', settings)
    paths = ('boot','mounts','isos','kickstarts')
    nginx = [f'server {{\n listen {ip}:8081;\n server_name _;\n client_max_body_size 1m;', ' location = /menu.ipxe { proxy_pass http://127.0.0.1:8080/menu.ipxe; }']
    nginx += [' location /'+kind+'/ { alias /var/lib/dockyard/'+kind+'/; autoindex off; }' for kind in paths]
    nginx += [' location / { return 404; }','}']
    (CONFIG/'dockyard-boot.nginx').write_text('\n'.join(nginx)+'\n')
    print('Configuration generated. No network service has been started.')
    print('Review /etc/dockyard/dnsmasq.conf and /etc/dockyard/dockyard-boot.nginx, then use the installation guide to activate on your approved provisioning network.')

def main():
    parser = argparse.ArgumentParser(description='Dockyard management')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('version')
    commands.add_parser('status')
    commands.add_parser('admin-password')
    cfg = commands.add_parser('configure-network')
    cfg.add_argument('--interface', required=True)
    cfg.add_argument('--server-ip', required=True)
    for arg in ('dhcp-start','dhcp-end','netmask','gateway','dns'):
        cfg.add_argument('--'+arg)
    args = parser.parse_args()
    if args.command == 'version':
        print('Dockyard 1.0.0')
    elif args.command == 'status':
        subprocess.run(['systemctl','status','dockyard','dockyard-dnsmasq','nginx','--no-pager'])
    elif args.command == 'configure-network':
        network(args)
    elif args.command == 'admin-password':
        root()
        password = getpass.getpass('New local administrator password (16+ characters): ')
        if len(password) < 16 or password != getpass.getpass('Confirm password: '):
            raise SystemExit('Password too short or confirmation did not match.')
        auth_path = CONFIG/'auth.json'
        settings = json.loads(auth_path.read_text())
        settings['password_hash'] = generate_password_hash(password)
        settings['auth_revision'] = secrets.token_hex(16)
        write_json(auth_path, settings, mode=0o640, owner='root')
        print('Password updated. Existing management sessions have been revoked.')

if __name__ == '__main__':
    main()
