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
    flat = []
    def walk(actions):
        for action in actions:
            flat.append(action)
            walk(action.children)
    walk(controller.GetRootActions())
    # find action 10982
    a10982 = [a for a in flat if a.eventId == 10982][0]
    controller.SetFrameEvent(10982, True)
    cpipe = controller.GetPipelineState()
    rw = cpipe.GetReadWriteResources(rd.ShaderStage.Compute, False)
    tiled_res = rw[0].descriptor.resource
    # Find all actions writing to tiled_res before 10982
    writes_to_tiled = [
        {'event': a.eventId, 'name': a.GetName(controller.GetStructuredFile()), 'flags': str(a.flags), 'copy_dst': str(a.copyDestination)}
        for a in flat
        if a.eventId < 10982 and (a.copyDestination == tiled_res or any(out == tiled_res for out in a.outputs))
    ]
    result['writes_to_tiled_buffer'] = writes_to_tiled
    names = {r.resourceId: r.name for r in controller.GetResources()}
    result['tiled_buf_name'] = names.get(tiled_res)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'find_writes_to_tiled.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
