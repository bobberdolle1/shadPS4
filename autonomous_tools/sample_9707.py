import json
from pathlib import Path
import sys
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import REPO  # noqa: E402
import renderdoc as rd

root = REPO / 'autonomous_logs' / 'xhigh-renderdoc-title-65s'
meta = json.loads((root / 'result.json').read_text())
cap = rd.OpenCaptureFile()
controller = None
result = {}
try:
    status = cap.OpenFile(meta['capture'], '', None)
    status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    tex_9707 = [t for t in controller.GetTextures() if str(t.resourceId) == 'ResourceId::9707'][0]
    tex_data = controller.GetTextureData(tex_9707.resourceId, rd.Subresource())
    result['tex_bytes'] = len(tex_data)
    import struct
    hwords = struct.unpack(f'<{len(tex_data)//2}H', tex_data)
    non_zero_pixels = []
    for pidx in range(len(hwords)//4):
        r, g, b, a = hwords[pidx*4 : pidx*4 + 4]
        if r != 0 or g != 0 or b != 0 or a != 0:
            x = pidx % tex_9707.width
            y = pidx // tex_9707.width
            non_zero_pixels.append({'x': x, 'y': y, 'rgba_half': [r, g, b, a]})
            if len(non_zero_pixels) >= 20:
                break
    result['non_zero_samples'] = non_zero_pixels
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'tex_9707_samples.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
