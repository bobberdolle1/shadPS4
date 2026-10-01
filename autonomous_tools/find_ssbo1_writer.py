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
    controller.SetFrameEvent(1973, True)
    cpipe = controller.GetPipelineState()
    rw = cpipe.GetReadWriteResources(rd.ShaderStage.Compute, False)
    # ssbo_1 buffer: rw[0]
    buf_res = rw[0].descriptor.resource
    buf_off = rw[0].descriptor.byteOffset
    # Search in all actions before 1973 for who wrote to buf_res
    flat = []
    def walk(actions):
        for action in actions:
            flat.append(action)
            walk(action.children)
    walk(controller.GetRootActions())
    writers = []
    for a in flat:
        if a.eventId < 1973:
            if a.copyDestination == buf_res or any(out == buf_res for out in a.outputs):
                writers.append({'event': a.eventId, 'name': a.GetName(controller.GetStructuredFile()), 'flags': str(a.flags)})
    result['writers_to_ssbo1_buffer'] = writers
    names = {r.resourceId: r.name for r in controller.GetResources()}
    result['buf_name'] = names.get(buf_res)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'find_ssbo1_writer.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
