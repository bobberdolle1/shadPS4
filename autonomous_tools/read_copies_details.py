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
    events = [1697, 1698, 1699, 1700, 1782, 1783, 1802, 2047, 2048, 2049, 2050]
    result['copies'] = []
    for ev in events:
        a = [act for act in flat if act.eventId == ev][0]
        result['copies'].append({
            'event': ev,
            'src_res': str(a.copySource),
            'dst_res': str(a.copyDestination),
        })
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'check_copies_details.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
