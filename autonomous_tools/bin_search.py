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
    buf_8978 = [b for b in controller.GetBuffers() if str(b.resourceId) == 'ResourceId::8978'][0]
    needle = b'\xe6\x32\xd7\x5c'
    flat = []
    def walk(actions):
        for action in actions:
            flat.append(action)
            walk(action.children)
    walk(controller.GetRootActions())
    # binary search between event 1 and 2047
    all_events = [a.eventId for a in flat if a.eventId <= 2047]
    low = 0
    high = len(all_events) - 1
    first_event_with_needle = None
    while low <= high:
        mid = (low + high) // 2
        ev = all_events[mid]
        controller.SetFrameEvent(ev, True)
        data = controller.GetBufferData(buf_8978.resourceId, 168493056, 4)
        if data == needle:
            first_event_with_needle = ev
            high = mid - 1
        else:
            low = mid + 1
    result['first_event_with_needle'] = first_event_with_needle
    if first_event_with_needle:
        a = [act for act in flat if act.eventId == first_event_with_needle][0]
        result['action_name'] = a.GetName(controller.GetStructuredFile())
        result['flags'] = str(a.flags)
        result['src'] = str(a.copySource)
        result['dst'] = str(a.copyDestination)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'binary_search_needle.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
