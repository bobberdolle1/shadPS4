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
    controller.SetFrameEvent(11035, True)
    pipe = controller.GetVulkanPipelineState()
    pc = pipe.pushconsts
    result['push_constants_hex'] = pc.hex() if pc else None
    result['push_constants_floats'] = [float(x) for x in pc] if pc else None
    import struct
    if pc and len(pc) >= 12:
        gamma, hdr, srgb_input = struct.unpack('<fII', pc[:12])
        result['unpacked'] = {'gamma': gamma, 'hdr': hdr, 'srgb_input': srgb_input}
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'pp_pass_push_consts.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
