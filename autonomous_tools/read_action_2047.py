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
    a2047 = [a for a in flat if a.eventId == 2047][0]
    result['action_name'] = a2047.GetName(controller.GetStructuredFile())
    result['src_res'] = str(a2047.copySource)
    result['dst_res'] = str(a2047.copyDestination)
    sd = controller.GetStructuredFile()
    for ev in a2047.events:
        if ev.eventId == 2047:
            chunk = sd.chunks[ev.chunkIndex]
            result['chunk_name'] = chunk.name
            break
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'action_2047.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
