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
    mod_actions = [a for a in flat if a.eventId in [11019, 11025]]
    result['draws'] = []
    for a in mod_actions:
        controller.SetFrameEvent(a.eventId, True)
        cpipe = controller.GetPipelineState()
        sci = [cpipe.GetScissor(i) for i in range(1)]
        vp = [cpipe.GetViewport(i) for i in range(1)]
        result['draws'].append({
            'event': a.eventId,
            'name': a.GetName(controller.GetStructuredFile()),
            'scissor': [{'x': s.x, 'y': s.y, 'w': s.width, 'h': s.height} for s in sci],
            'viewport': [{'x': v.x, 'y': v.y, 'w': v.width, 'h': v.height} for v in vp],
            'num_indices': a.numIndices,
            'num_instances': a.numInstances,
        })
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'draws_viewports.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
