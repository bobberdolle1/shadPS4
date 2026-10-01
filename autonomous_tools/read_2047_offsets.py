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
    a2047 = [act for act in flat if act.eventId == 2047][0]
    controller.SetFrameEvent(2047, True)
    buf_15055 = [b for b in controller.GetBuffers() if str(b.resourceId) == 'ResourceId::15055'][0]
    needle = b'\xe6\x32\xd7\x5c'
    # We saw needle was at 30140 in 15055!
    # Offset in dst = 168493056 (0xa0b0000).
    result['src_needle_offset'] = 30140
    result['dst_needle_offset'] = 168493056
    result['diff'] = 168493056 - 30140
    result['diff_hex'] = hex(168493056 - 30140)
    # Check surrounding words in 15055 around 30140
    raw = controller.GetBufferData(buf_15055.resourceId, 30140 - 64, 256)
    result['raw_around_needle_hex'] = raw.hex()
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'check_2047_offsets.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
