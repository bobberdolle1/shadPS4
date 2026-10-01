import json
import os
import struct
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import REPO  # noqa: E402
import renderdoc as rd

root = Path(os.environ.get('SCAN_DIR',
                           str(REPO / 'autonomous_logs/xhigh-renderdoc-title-65s')))
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
    cands = [t for t in controller.GetTextures()
             if t.width == 1004 and t.height == 319
             and 'R16G16B16A16' in t.format.Name()]
    result['candidate_count'] = len(cands)
    entries = []
    for tex in cands:
        data = controller.GetTextureData(tex.resourceId, rd.Subresource(0, 0, 0))
        counts = {}
        for i in range(0, len(data) - 7, 8):
            k = struct.unpack_from('<4H', data, i)
            counts[k] = counts.get(k, 0) + 1
        top = sorted(counts.items(), key=lambda kv: -kv[1])[:4]
        entries.append({
            'id': str(tex.resourceId),
            'name': resnames.get(tex.resourceId),
            'distinct_texels': len(counts),
            'top': [{'halves': list(k), 'count': v,
                     'floats': list(struct.unpack('<4e', struct.pack('<4H', *k)))}
                    for k, v in top],
        })
        path = root / f'tex_{str(tex.resourceId).replace(":", "_")}.png'
        tex.Save(0, str(path))
        entries[-1]['png'] = path.name
    result['textures'] = entries
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'tex_census.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
