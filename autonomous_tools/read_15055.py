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
    # Check buffer 15055 data
    buf_15055 = [b for b in controller.GetBuffers() if str(b.resourceId) == 'ResourceId::15055'][0]
    raw = controller.GetBufferData(buf_15055.resourceId, 0, 0)
    result['buf_15055_len'] = len(raw)
    needle = b'\xe6\x32\xd7\x5c'
    result['needle_in_15055'] = raw.find(needle)
    names = {r.resourceId: r.name for r in controller.GetResources()}
    result['name_15055'] = names.get(buf_15055.resourceId)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'check_15055.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
