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
    controller.SetFrameEvent(11019, True)
    cpipe = controller.GetPipelineState()
    rw = cpipe.GetReadWriteResources(rd.ShaderStage.Pixel, False)
    raw = controller.GetBufferData(rw[0].descriptor.resource, rw[0].descriptor.byteOffset, rw[0].descriptor.byteSize)
    import struct
    dwords = [struct.unpack('<I', raw[i:i+4])[0] for i in range(0, len(raw), 4)]
    result['dwords_hex'] = [f"0x{dw:08x}" for dw in dwords]
    result['floats'] = [struct.unpack('<f', raw[i:i+4])[0] for i in range(0, len(raw), 4)]
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'draw_11019_ssbo_dwords.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
