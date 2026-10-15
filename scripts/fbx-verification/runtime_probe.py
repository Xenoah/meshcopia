"""Execute only in future CI; reads installed runtime, does not convert assets."""
import bpy, numpy as np, sys, json, platform, zlib, hashlib, os
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:];expected=json.loads(Path(args[0]).read_text());v=expected['versions']
assert bpy.app.version_string==v['blender'] and sys.version.split()[0]==v['python'] and np.__version__==v['numpy'] and zlib.ZLIB_RUNTIME_VERSION==v['zlib']
assert platform.libc_ver()==('glibc',v['glibc'])
assert os.environ.get('PYTHONHASHSEED')=='0' and not sys.flags.hash_randomization
h=hashlib.sha256(Path(bpy.app.binary_path).read_bytes()).hexdigest();assert h==expected['binarySha256']
r={'blender':bpy.app.version_string,'blenderBuildHash':bpy.app.build_hash.decode(),'blenderBinarySha256':h,'python':sys.version,'numpy':np.__version__,'zlib':zlib.ZLIB_RUNTIME_VERSION,'platform':platform.platform()}
Path(args[1]).write_text(json.dumps(r,indent=2)+'\n')
