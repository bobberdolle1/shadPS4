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
    tex_9707 = [t for t in controller.GetTextures() if str(t.resourceId) == 'ResourceId::9707'][0]
    result['tex'] = {
        'id': str(tex_9707.resourceId),
        'w': tex_9707.width,
        'h': tex_9707.height,
        'format': tex_9707.format.Name(),
    }
    sub = rd.Subresource()
    history = controller.PixelHistory(tex_9707.resourceId, 50, 600, sub, rd.CompType.Typeless)
    result['history'] = []
    for mod in history:
        result['history'].append({
            'event': mod.eventId,
            'passed': mod.Passed(),
            'pre': list(mod.preMod.col.floatValue),
            'post': list(mod.postMod.col.floatValue),
            'out': list(mod.shaderOut.col.floatValue) if mod.shaderOut.IsValid() else None,
            'prim': mod.primitiveID,
        })
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'trace_9707_producer.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
