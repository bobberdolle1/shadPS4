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
    controller.SetFrameEvent(10984, True)
    cpipe = controller.GetPipelineState()
    flat = []
    def walk(actions):
        for action in actions:
            flat.append(action)
            walk(action.children)
    walk(controller.GetRootActions())
    a10984 = [a for a in flat if a.eventId == 10984][0]
    result['src_buffer'] = str(a10984.copySource)
    result['dst_image'] = str(a10984.copyDestination)
    sd = controller.GetStructuredFile()
    chunk = None
    for ev in a10984.events:
        if ev.eventId == 10984:
            chunk = sd.chunks[ev.chunkIndex]
            break
    if chunk:
        result['chunk_name'] = chunk.name
        params = {}
        for p in chunk.subData:
            params[p.name] = str(p.value)
        result['chunk_params'] = params
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'copy_10984.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
