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
    a10984 = [a for a in flat if a.eventId == 10984][0]
    src_buf_id = a10984.copySource
    # Search in 16MB buffer for 13030 (0x32e6)
    buf_data = controller.GetBufferData(src_buf_id, 0, 0)
    result['buffer_size'] = len(buf_data)
    needle = b'\xe6\x32\xd7\x5c'
    idx = buf_data.find(needle)
    result['needle_offset'] = idx
    if idx != -1:
        # Check coordinates in 1004 x 319 image (8 bytes per pixel)
        result['pixel_index'] = idx // 8
        result['x'] = (idx // 8) % 1004
        result['y'] = (idx // 8) // 1004
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'find_green_in_buffer.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
