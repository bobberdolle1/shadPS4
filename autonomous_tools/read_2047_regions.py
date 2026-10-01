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
    sd = controller.GetStructuredFile()
    chunk = sd.chunks[a2047.events[-1].chunkIndex]
    def serialize_sd(node):
        d = {'name': node.name}
        if node.NumChildren() > 0:
            d['children'] = [serialize_sd(node.GetChild(i)) for i in range(node.NumChildren())]
        else:
            try:
                d['val'] = node.AsString()
            except:
                pass
        return d
    result['chunk_2047'] = serialize_sd(chunk)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'chunk_2047_regions.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
