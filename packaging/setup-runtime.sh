#!/bin/bash
set -euo pipefail
umask 022
python3 -m venv /opt/dockyard/venv
/opt/dockyard/venv/bin/pip install --no-index --only-binary=:all: --find-links=/opt/dockyard/wheels -r /opt/dockyard/requirements.lock
/opt/dockyard/venv/bin/pip check
install -d -m 0750 -o root -g dockyard /etc/dockyard
install -d -m 0755 -o dockyard -g dockyard /var/lib/dockyard
for name in isos boot mounts kickstarts tftp tftp/ipxe; do install -d -m 0755 -o dockyard -g dockyard "/var/lib/dockyard/$name"; done
install -d -m 0700 -o dockyard -g dockyard /var/lib/dockyard/config
install -d -m 0750 -o dnsmasq -g dnsmasq /var/lib/dockyard/network
/opt/dockyard/venv/bin/python - <<'PY'
import os,json,secrets,pwd
from pathlib import Path
from werkzeug.security import generate_password_hash
config=Path('/etc/dockyard'); data=Path('/var/lib/dockyard')
account=pwd.getpwnam('dockyard')
def create(path, text, mode, owner=0, group=account.pw_gid):
 if path.exists():return
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,mode)
 with os.fdopen(fd,'w') as out:out.write(text)
 os.chown(path,owner,group)
create(config/'session.key',secrets.token_hex(32)+'\n',0o640)
if not (config/'auth.json').exists():
 password=secrets.token_urlsafe(24)
 create(config/'auth.json',json.dumps(dict(username='admin',password_hash=generate_password_hash(password),ldap_enabled=False),indent=2),0o640)
 create(data/'admin.password',password+'\n',0o600,group=0)
create(data/'config/menu.json',json.dumps(dict(title='Dockyard Boot Menu',timeout=60,default='',entries=[]),indent=2),0o600,account.pw_uid)
create(data/'config/settings.json',json.dumps(dict(server_ip='127.0.0.1',web_port=8080,boot_port=8081,dhcp_enabled=False,version='1.0.0'),indent=2),0o600,account.pw_uid)
PY
install -m 0644 /opt/dockyard/ipxe/undionly.kpxe /var/lib/dockyard/tftp/ipxe/undionly.kpxe
install -m 0644 /opt/dockyard/ipxe/ipxe.efi /var/lib/dockyard/tftp/ipxe/ipxe.efi
echo 'Dockyard installed. Read /var/lib/dockyard/admin.password privately as root, then enable dockyard.service.'
echo 'DHCP/TFTP and boot HTTP remain inactive until explicitly configured and enabled.'
