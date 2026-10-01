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
    # Guest address was 0x100a0b0000.
    # Buffer base was 0x1000000000.
    # Offset in buffer = 168493056 bytes.
    # Look at actions before 2047: 1782, 1783, 1802, etc.
    sd = controller.GetStructuredFile()
    events = [1782, 1783, 1802, 2047]
    for ev in events:
        a = [act for act in flat if act.eventId == ev][0]
        result[str(ev)] = {
            'name': a.GetName(sd),
            'src': str(a.copySource),
            'dst': str(a.copyDestination),
        }
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'check_actions_before_2047.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
