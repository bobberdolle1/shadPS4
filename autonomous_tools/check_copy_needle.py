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
    flat = []
    def walk(actions):
        for action in actions:
            flat.append(action)
            walk(action.children)
    walk(controller.GetRootActions())
    events = [1697, 1698, 1699, 1700, 1782, 1783, 1802, 2047, 2048, 2049, 2050]
    # Check data in 8978 after each event at offset 168493056
    needle = b'\xe6\x32\xd7\x5c'
    buf_8978 = [b for b in controller.GetBuffers() if str(b.resourceId) == 'ResourceId::8978'][0]
    result['findings'] = []
    for ev in events:
        controller.SetFrameEvent(ev, True)
        data = controller.GetBufferData(buf_8978.resourceId, 168493056, 32)
        has_needle = (data[:4] == needle)
        result['findings'].append({'event': ev, 'has_needle': has_needle, 'hex': data[:16].hex()})
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'check_copy_needle.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
