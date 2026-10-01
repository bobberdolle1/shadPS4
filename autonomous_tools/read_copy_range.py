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
    offset_in_buf = 0x100a0b0000 - 0x1000000000
    result['guest_offset_in_buf'] = offset_in_buf
    # Buffer 8978
    buf_8978 = [b for b in controller.GetBuffers() if str(b.resourceId) == 'ResourceId::8978'][0]
    target_id = buf_8978.resourceId
    copies = []
    for a in flat:
        if a.copyDestination == target_id:
            copies.append({'event': a.eventId, 'name': a.GetName(controller.GetStructuredFile()), 'src': str(a.copySource)})
    result['copies'] = copies
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'find_copy_region.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
