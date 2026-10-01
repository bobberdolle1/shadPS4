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
    # Check linear scan between 1940 and 2047
    events = [1940, 1950, 1980, 2000, 2020, 2040, 2045, 2046, 2047]
    result['scan'] = []
    for ev in events:
        controller.SetFrameEvent(ev, True)
        d = controller.GetBufferData(buf_8978.resourceId, 168493056, 4)
        result['scan'].append({'event': ev, 'hex': d.hex()})
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'linear_scan_needle.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
