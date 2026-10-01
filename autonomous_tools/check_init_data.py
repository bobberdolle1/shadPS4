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
    buf_8978 = [b for b in controller.GetBuffers() if str(b.resourceId) == 'ResourceId::8978'][0]
    needle = b'\xe6\x32\xd7\x5c'
    # Check event 0
    controller.SetFrameEvent(1, True)
    data = controller.GetBufferData(buf_8978.resourceId, 168493056, 32)
    result['has_needle_at_event_1'] = (data[:4] == needle)
    result['hex_at_event_1'] = data[:16].hex()
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'check_init_data.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
