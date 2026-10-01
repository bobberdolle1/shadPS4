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
    sd = controller.GetStructuredFile()
    for ev in a10984.events:
        if ev.eventId == 10984:
            chunk = sd.chunks[ev.chunkIndex]
            result['chunk_name'] = chunk.name
            result['data_type'] = str(type(chunk.data))
            result['data_repr'] = repr(chunk.data)
            def dump_obj(obj):
                d = {'name': obj.name, 'type': str(obj.type.basetype)}
                if obj.NumChildren() > 0:
                    d['children'] = [dump_obj(obj.GetChild(i)) for i in range(obj.NumChildren())]
                else:
                    try:
                        d['val'] = str(obj.value)
                    except:
                        pass
                return d
            result['structured'] = dump_obj(chunk.data)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'chunk_10984_fixed.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
