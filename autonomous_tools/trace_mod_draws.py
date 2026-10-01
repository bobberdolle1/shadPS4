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
    mod_actions = [a for a in flat if a.eventId in [10451, 11019, 11025]]
    result['actions'] = []
    for a in mod_actions:
        controller.SetFrameEvent(a.eventId, True)
        pipe = controller.GetVulkanPipelineState()
        refl = pipe.fragmentShader.reflection
        result['actions'].append({
            'event': a.eventId,
            'name': a.GetName(controller.GetStructuredFile()),
            'pipeline': str(pipe.graphics.pipelineResourceId),
            'shader': str(pipe.fragmentShader.resourceId),
            'ps_name': refl.entryPoint if refl else None,
            'ro': [{'name': r.name, 'bind': r.bindArraySize} for r in refl.readOnlyResources] if refl else [],
        })
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'draws_modifying_599.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
