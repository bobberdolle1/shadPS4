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
    sd = controller.GetStructuredFile()
    window = []
    for a in flat:
        if 10940 <= a.eventId <= 11030:
            window.append({
                'event': a.eventId,
                'name': a.GetName(sd),
                'flags': str(a.flags),
                'outputs': [str(o) for o in a.outputs],
                'copy_src': str(a.copySource),
                'copy_dst': str(a.copyDestination),
            })
    result['window'] = window
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'events_window.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
