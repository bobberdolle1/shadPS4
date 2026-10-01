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
    buf_8978 = [b for b in controller.GetBuffers() if str(b.resourceId) == 'ResourceId::8978'][0]
    needle = b'\xe6\x32\xd7\x5c'
    events = list(range(1950, 1981))
    first = None
    for ev in events:
        controller.SetFrameEvent(ev, True)
        d = controller.GetBufferData(buf_8978.resourceId, 168493056, 4)
        if d == needle:
            first = ev
            break
    result['exact_first_event'] = first
    if first:
        flat = []
        def walk(actions):
            for action in actions:
                flat.append(action)
                walk(action.children)
        walk(controller.GetRootActions())
        a = [act for act in flat if act.eventId == first][0]
        result['action_name'] = a.GetName(controller.GetStructuredFile())
        result['flags'] = str(a.flags)
        result['src'] = str(a.copySource)
        result['dst'] = str(a.copyDestination)
        cpipe = controller.GetPipelineState()
        ro = cpipe.GetReadOnlyResources(rd.ShaderStage.Compute, False)
        rw = cpipe.GetReadWriteResources(rd.ShaderStage.Compute, False)
        result['rw'] = [{'res': str(u.descriptor.resource), 'offset': u.descriptor.byteOffset, 'size': u.descriptor.byteSize} for u in rw]
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'exact_needle_event.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
