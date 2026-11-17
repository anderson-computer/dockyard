"""Authenticated loopback development preview. Install packaging/requirements.txt first."""
import os,json,secrets
from pathlib import Path
from werkzeug.security import generate_password_hash
root=Path(os.environ.get('DOCKYARD_DEV_DIR','./dockyard-state')).resolve()
os.umask(0o077)
root.mkdir(parents=True,exist_ok=True)
config=root/'private';config.mkdir(exist_ok=True)
for name in ('isos','kickstarts','boot','mounts','config'):(root/name).mkdir(exist_ok=True)
if not (config/'session.key').exists():(config/'session.key').write_text(secrets.token_hex(32))
if not (config/'auth.json').exists():
 password=secrets.token_urlsafe(24)
 (config/'auth.json').write_text(json.dumps(dict(username='admin',password_hash=generate_password_hash(password))))
 (root/'admin.password').write_text(password)
os.environ['DOCKYARD_DIR']=str(root)
os.environ['DOCKYARD_CONFIG']=str(config)
from app import app
print('Read the private admin.password file in the development state directory to sign in.')
app.run(host='127.0.0.1',port=8080,debug=False)
