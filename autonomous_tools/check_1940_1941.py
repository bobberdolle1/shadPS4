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
    # Check event 1940
    controller.SetFrameEvent(1940, True)
    d1940 = controller.GetBufferData(buf_8978.resourceId, 168493056, 4)
    # Check event 1941
    controller.SetFrameEvent(1941, True)
    d1941 = controller.GetBufferData(buf_8978.resourceId, 168493056, 4)
    result['at_1940'] = d1940.hex()
    result['at_1941'] = d1941.hex()
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'check_1940_1941.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
