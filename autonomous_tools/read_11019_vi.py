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
    ds = pipe.graphics.descriptorSets[0]
    result['layout'] = str(ds.layoutResourceId)
    # Check vertex attributes
    vi = pipe.vertexInput
    result['bindings'] = [{'stride': b.byteStride, 'rate': str(b.rate)} for b in vi.bindings]
    result['attributes'] = [{'loc': a.location, 'binding': a.binding, 'format': a.format.Name(), 'offset': a.byteOffset} for a in vi.attributes]
    vbufs = pipe.vertexInput.vertexBuffers
    result['vbufs'] = [{'res': str(vb.resourceId), 'offset': vb.byteOffset, 'size': vb.byteSize} for vb in vbufs]
    if vbufs and vbufs[0].resourceId != rd.ResourceId():
        raw_vb = controller.GetBufferData(vbufs[0].resourceId, vbufs[0].byteOffset, min(vbufs[0].byteSize, 1024))
        result['raw_vb_len'] = len(raw_vb)
        import struct
        floats = [struct.unpack('<f', raw_vb[i:i+4])[0] for i in range(0, min(len(raw_vb), 128), 4)]
        result['vb_floats'] = floats
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'draw_11019_vertex_input.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
