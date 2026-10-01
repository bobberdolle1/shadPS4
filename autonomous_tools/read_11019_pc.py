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
    controller.SetFrameEvent(11019, True)
    pipe = controller.GetVulkanPipelineState()
    pc = pipe.pushconsts
    result['push_consts_len'] = len(pc) if pc else 0
    import struct
    dws = [struct.unpack('<I', pc[i:i+4])[0] for i in range(0, len(pc), 4)]
    result['dwords_hex'] = [f"0x{d:08x}" for d in dws]
    result['floats'] = [struct.unpack('<f', pc[i:i+4])[0] for i in range(0, len(pc), 4)]
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'draw_11019_push_consts.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
