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
    pipe = controller.GetVulkanPipelineState()
    ds = pipe.graphics.descriptorSets[0]
    result['desc_set'] = str(ds.descriptorSetResourceId)
    cpipe = controller.GetPipelineState()
    ro = cpipe.GetReadOnlyResources(rd.ShaderStage.Pixel, False)
    cb = cpipe.GetConstantBlocks(rd.ShaderStage.Pixel, False)
    rw = cpipe.GetReadWriteResources(rd.ShaderStage.Pixel, False)
    result['ro'] = [{'res': str(u.descriptor.resource), 'view': str(u.descriptor.view), 'fmt': u.descriptor.format.Name()} for u in ro]
    result['cb'] = [{'res': str(u.descriptor.resource), 'offset': u.descriptor.byteOffset, 'size': u.descriptor.byteSize} for u in cb]
    result['rw'] = [{'res': str(u.descriptor.resource), 'offset': u.descriptor.byteOffset, 'size': u.descriptor.byteSize} for u in rw]
    ssbo_res = rw[0].descriptor.resource if rw else None
    if ssbo_res:
        raw = controller.GetBufferData(ssbo_res, rw[0].descriptor.byteOffset, rw[0].descriptor.byteSize)
        result['ssbo_bytes_len'] = len(raw)
        import struct
        floats = [struct.unpack('<f', raw[i:i+4])[0] for i in range(0, min(len(raw), 128), 4)]
        result['ssbo_floats'] = floats
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'draw_11019_resources.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
