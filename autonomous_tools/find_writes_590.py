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
    flat = []
    def walk(actions):
        for action in actions:
            flat.append(action)
            walk(action.children)
    walk(controller.GetRootActions())
    a10984 = [a for a in flat if a.eventId == 10984][0]
    # Check all actions before 10984 that write to buffer 590
    writes_to_590 = [
        {'event': a.eventId, 'name': a.GetName(controller.GetStructuredFile()), 'flags': str(a.flags)}
        for a in flat
        if a.eventId < 10984 and (a.copyDestination == a10984.copySource or any(out == a10984.copySource for out in a.outputs))
    ]
    result['writes_to_src_buf'] = writes_to_590
    names = {r.resourceId: r.name for r in controller.GetResources()}
    result['src_buf_name'] = names.get(a10984.copySource)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'writes_to_590.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
