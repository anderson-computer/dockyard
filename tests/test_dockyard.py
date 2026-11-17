import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path('/opt/dockyard') if os.environ.get('DOCKYARD_TEST_INSTALLED') else Path(__file__).resolve().parents[1]
test_root = tempfile.TemporaryDirectory(prefix='dockyard-tests-')
state = Path(test_root.name)
config = state/'private-config'
config.mkdir(mode=0o700)
os.environ.update(DOCKYARD_DIR=str(state/'data'), DOCKYARD_CONFIG=str(config), DOCKYARD_SECRET_KEY='synthetic-session-key-for-dockyard-tests-01')
sys.path.insert(0, str(ROOT/'web'))
from werkzeug.security import generate_password_hash
(config/'auth.json').write_text(json.dumps(dict(username='admin', password_hash=generate_password_hash('SyntheticAdmin12345!'), ldap_enabled=False)))
import app as backend
from security import validate_menu, validate_settings

class DockyardTests(unittest.TestCase):
    def setUp(self):
        for directory in [backend.ISOS_DIR,backend.KS_DIR,backend.BOOT_DIR,backend.MOUNTS_DIR,backend.CONFIG_DIR]:
            Path(directory).mkdir(parents=True,exist_ok=True)
        backend.save_json(backend.MENU_JSON, dict(title='Dockyard', timeout=60, default='', entries=[]))
        self.client = backend.app.test_client()

    def login(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as session:
            token = session['csrf']
        response = self.client.post('/login', data=dict(username='admin',password='SyntheticAdmin12345!',csrf_token=token))
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as session:
            return {'X-CSRF-Token':session['csrf']}

    def test_anonymous_management_denied_but_boot_menu_available(self):
        self.assertEqual(self.client.get('/api/settings').status_code,401)
        self.assertEqual(self.client.get('/').status_code,302)
        self.assertEqual(self.client.get('/menu.ipxe').status_code,200)
        self.assertEqual(self.client.get('/healthz').json['application'],'Dockyard')

    def test_session_csrf_and_origin_boundaries(self):
        headers=self.login()
        self.assertEqual(self.client.get('/api/status').status_code,200)
        self.assertEqual(self.client.put('/api/settings',json={'server_ip':'127.0.0.1'}).status_code,403)
        self.assertEqual(self.client.put('/api/settings',json={'server_ip':'127.0.0.1'},headers=dict(headers,Origin='http://other.example')).status_code,403)
        self.assertEqual(self.client.put('/api/settings',json={'server_ip':'127.0.0.1','dhcp_enabled':False},headers=headers).status_code,200)
        self.assertEqual(self.client.post('/logout',headers=headers).status_code,302)
        self.assertEqual(self.client.get('/api/menu').status_code,401)

    def test_upload_and_kickstart_path_traversal_rejected(self):
        headers=self.login()
        for name in ('../../outside.iso','/tmp/outside.iso','bad*.iso'):
            response=self.client.post('/api/images/upload',data={'file':(io.BytesIO(b'ISO'),name)},headers=headers)
            self.assertEqual(response.status_code,400,name)
        for name in ('../../outside.ks','/tmp/outside.ks','bad\\file.ks'):
            response=self.client.post('/api/kickstarts/upload',json={'name':name,'content':'not saved'},headers=headers)
            self.assertEqual(response.status_code,400,name)
        self.assertFalse((state/'outside.ks').exists())

    def test_symlink_escape_rejected(self):
        headers=self.login()
        outside=state/'outside.txt';outside.write_text('keep')
        link=Path(backend.KS_DIR,'escape.ks')
        link.symlink_to(outside)
        try:
            self.assertEqual(self.client.put('/api/kickstarts/escape.ks',json={'content':'changed'},headers=headers).status_code,400)
            self.assertEqual(outside.read_text(),'keep')
        finally:
            link.unlink()

    def test_menu_injection_and_auth_settings_rejected(self):
        headers=self.login()
        invalid=dict(title='menu\nchain http://untrusted',entries=[])
        self.assertEqual(self.client.put('/api/menu',json=invalid,headers=headers).status_code,400)
        self.assertEqual(self.client.put('/api/settings',json={'ldap_password':'never save'},headers=headers).status_code,400)
        self.assertEqual(self.client.post('/api/menu/entries',json={'id':'../../bad','iso_id':'test','label':'bad'},headers=headers).status_code,400)

    def test_menu_template_escaping_and_public_generation(self):
        headers=self.login()
        entry=dict(id='test-image',iso_id='test-image',label='Sample "quoted" image',os_type='rhel',enabled=False)
        self.assertEqual(self.client.post('/api/menu/entries',json=entry,headers=headers).status_code,200)
        html=self.client.get('/menu-builder').get_data(as_text=True)
        from html.parser import HTMLParser
        handlers=[]
        class Buttons(HTMLParser):
            def handle_starttag(self, tag, attrs):
                value=dict(attrs).get('onclick','')
                if value.startswith('editEntry('):handlers.append(value)
        Buttons().feed(html)
        self.assertTrue(handlers)
        self.assertIn('"id": "test-image"', handlers[0])
        script=self.client.get('/menu.ipxe').get_data(as_text=True)
        self.assertNotIn(':test-image',script)
        self.assertEqual(self.client.put('/api/menu/entries/test-image',json={'enabled':True},headers=headers).status_code,200)
        script=self.client.get('/menu.ipxe').get_data(as_text=True)
        self.assertIn(':test-image',script)
        self.assertIn(':8081/boot/test-image/vmlinuz',script)
        self.assertEqual(script.splitlines().count(':menu'),1)
        self.assertIn('boot\ngoto menu',script)

    def test_status_poll_does_not_enable_boot_entry(self):
        headers=self.login()
        entry=dict(id='pending',iso_id='pending',label='Pending',enabled=False)
        backend.save_json(backend.MENU_JSON,dict(entries=[entry]))
        backend.EXTRACT_STATUS['pending']=dict(status='done',progress=100,message='done')
        self.assertEqual(self.client.get('/api/images/pending/extract/status').status_code,200)
        self.assertFalse(backend.get_menu()['entries'][0]['enabled'])

    def test_no_privileged_restart_from_web(self):
        headers=self.login()
        with patch.object(backend.subprocess,'run') as run:
            response=self.client.post('/api/service/dnsmasq/restart',headers=headers)
            self.assertEqual(response.status_code,409)
            run.assert_not_called()

    def test_iso_extraction_in_userspace(self):
        if not shutil.which('bsdtar'):
            self.skipTest('ISO tools unavailable')
        source=state/'iso-source';(source/'images/pxeboot').mkdir(parents=True,exist_ok=True)
        (source/'BaseOS').mkdir(exist_ok=True)
        (source/'images/pxeboot/vmlinuz').write_bytes(b'synthetic-kernel')
        (source/'images/pxeboot/initrd.img').write_bytes(b'synthetic-initrd')
        image=Path(backend.ISOS_DIR,'extract-test.iso')
        shutil.copyfile(Path(__file__).parent/'fixtures/boot-smoke.iso', image)
        backend._do_extract('extract-test',str(image))
        self.assertEqual(backend.EXTRACT_STATUS['extract-test']['status'],'done',backend.EXTRACT_STATUS['extract-test'])
        self.assertEqual(Path(backend.BOOT_DIR,'extract-test/vmlinuz').read_bytes(),b'synthetic-kernel')

    def test_help_about_and_no_cdn_resources(self):
        for route in ('/help','/about'):
            response=self.client.get(route)
            self.assertEqual(response.status_code,200)
            self.assertIn(b'Dockyard',response.data)
        for path in (ROOT/'web/templates').glob('*.html'):
            text=path.read_text()
            self.assertNotRegex(text,r'(?:src|href)=["\']https?://(?:cdn|cdnjs)')

    def test_ldap_tls_and_filter_escaping(self):
        import auth
        conn=MagicMock()
        conn.search_s.return_value=[('uid=test',{'memberOf':[b'cn=dockyard-admins,cn=groups,cn=accounts,dc=example,dc=com']})]
        handler=auth.FreeIPAAuth('ldap.example.com','dc=example,dc=com')
        with patch.object(auth.ldap,'initialize',return_value=conn):
            self.assertTrue(handler.authenticate_admin('test','synthetic-password'))
            self.assertLess([call[0] for call in conn.method_calls].index('start_tls_s'),[call[0] for call in conn.method_calls].index('simple_bind_s'))
            conn.unbind_s.assert_called()

    def test_password_revision_revokes_session(self):
        self.login()
        auth_path=config/'auth.json'
        original=auth_path.read_text()
        try:
            changed=json.loads(original)
            changed['auth_revision']='new-test-revision'
            auth_path.write_text(json.dumps(changed))
            self.assertEqual(self.client.get('/api/menu').status_code,401)
        finally:
            auth_path.write_text(original)

if __name__=='__main__':unittest.main(verbosity=2)
