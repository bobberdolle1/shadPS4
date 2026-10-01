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
    vbs = cpipe.GetVBuffers()
    result['vbuffers'] = [{'res': str(vb.resourceId), 'byteOffset': vb.byteOffset, 'byteSize': vb.byteSize, 'byteStride': vb.byteStride} for vb in vbs]
    attrs = cpipe.GetVertexInputs()
    result['attributes'] = [{'format': a.format.Name(), 'byteOffset': a.byteOffset, 'vb': a.vertexBuffer} for a in attrs]
    if vbs and vbs[0].resourceId != rd.ResourceId():
        raw_vb = controller.GetBufferData(vbs[0].resourceId, vbs[0].byteOffset, min(vbs[0].byteSize, 1024))
        import struct
        floats = [struct.unpack('<f', raw_vb[i:i+4])[0] for i in range(0, min(len(raw_vb), 128), 4)]
        result['vb_floats'] = floats
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'draw_11019_vbuffers.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
