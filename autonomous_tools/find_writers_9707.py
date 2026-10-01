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
    tex_9707 = [t for t in controller.GetTextures() if str(t.resourceId) == 'ResourceId::9707'][0]
    target_id = tex_9707.resourceId
    writes_to_9707 = [
        {'event': a.eventId, 'name': a.GetName(controller.GetStructuredFile()), 'flags': str(a.flags), 'copy_dst': str(a.copyDestination)}
        for a in flat
        if a.copyDestination == target_id or any(out == target_id for out in a.outputs)
    ]
    result['writes'] = writes_to_9707
    names = {r.resourceId: r.name for r in controller.GetResources()}
    result['name_9707'] = names.get(target_id)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'actions_writing_9707.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
