"""Generate a tiny synthetic ISO fixture for unprivileged extraction tests."""
import io
from pathlib import Path
import pycdlib
destination=Path(__file__).resolve().parents[1]/'tests/fixtures'
destination.mkdir(parents=True,exist_ok=True)
iso=pycdlib.PyCdlib()
iso.new(interchange_level=3,rock_ridge='1.09')
iso.add_directory('/IMAGES',rr_name='images')
iso.add_directory('/IMAGES/PXEBOOT',rr_name='pxeboot')
iso.add_directory('/BASEOS',rr_name='BaseOS')
iso.add_fp(io.BytesIO(b'synthetic-kernel'),len(b'synthetic-kernel'),iso_path='/IMAGES/PXEBOOT/VMLINUZ.;1',rr_name='vmlinuz')
iso.add_fp(io.BytesIO(b'synthetic-initrd'),len(b'synthetic-initrd'),iso_path='/IMAGES/PXEBOOT/INITRD.IMG;1',rr_name='initrd.img')
iso.write(str(destination/'boot-smoke.iso'))
iso.close()
