import json
from pathlib import Path
import sys
import renderdoc as rd

root = Path('E:/programming/shadPS4/autonomous_logs/xhigh-renderdoc-title-65s')
meta = json.loads((root / 'result.json').read_text())
cap = rd.OpenCaptureFile()
controller = None
result = {}
try:
    status = cap.OpenFile(meta['capture'], '', None)
    status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    target_599 = [t for t in controller.GetTextures() if str(t.resourceId) == 'ResourceId::599'][0]
    tex_170 = [t for t in controller.GetTextures() if str(t.resourceId) == 'ResourceId::170'][0]
    sub = rd.Subresource()
    h599 = controller.PixelHistory(target_599.resourceId, 250, 700, sub, rd.CompType.Typeless)
    result['h599_250_700'] = [{'event': m.eventId, 'passed': m.Passed(), 'post': list(m.postMod.col.floatValue)} for m in h599]
    h170 = controller.PixelHistory(tex_170.resourceId, 250, 700, sub, rd.CompType.Typeless)
    result['h170_250_700'] = [{'event': m.eventId, 'passed': m.Passed(), 'post': list(m.postMod.col.floatValue)} for m in h170]
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'trace_250_700.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
