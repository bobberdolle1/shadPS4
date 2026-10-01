import json
import os
from pathlib import Path
import renderdoc as rd

root = Path(os.environ.get('SCAN_DIR',
                           'E:/programming/shadPS4/autonomous_logs/xhigh-renderdoc-title-65s'))
meta = json.loads((root / 'result.json').read_text())
cap = rd.OpenCaptureFile()
controller = None
result = {}
try:
    status = cap.OpenFile(meta['capture'], '', None)
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    resnames = {r.resourceId: r.name for r in controller.GetResources()}
    pat = b'\xe6\x32\xd7\x5c'
    inv = []
    for tex in controller.GetTextures():
        if 'R16G16B16A16' not in tex.format.Name():
            continue
        data = controller.GetTextureData(tex.resourceId, rd.Subresource(0, 0, 0))
        count = sum(1 for i in range(0, len(data) - 3, 8) if data[i:i + 4] == pat)
        inv.append({'id': str(tex.resourceId), 'size': [tex.width, tex.height],
                    'name': resnames.get(tex.resourceId),
                    'pattern_words': count, 'texels': tex.width * tex.height})
    result['rgba16f_textures'] = inv
    result['count'] = len(inv)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'rgba16f_inventory.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
