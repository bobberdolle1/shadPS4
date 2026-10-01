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
    controller.SetFrameEvent(10982, True)
    cpipe = controller.GetPipelineState()
    ro = cpipe.GetReadOnlyResources(rd.ShaderStage.Compute, False)
    rw = cpipe.GetReadWriteResources(rd.ShaderStage.Compute, False)
    cb = cpipe.GetConstantBlocks(rd.ShaderStage.Compute, False)
    result['ro'] = [{'res': str(u.descriptor.resource), 'offset': u.descriptor.byteOffset, 'size': u.descriptor.byteSize} for u in ro]
    result['rw'] = [{'res': str(u.descriptor.resource), 'offset': u.descriptor.byteOffset, 'size': u.descriptor.byteSize} for u in rw]
    result['cb'] = [{'res': str(u.descriptor.resource), 'offset': u.descriptor.byteOffset, 'size': u.descriptor.byteSize} for u in cb]
    pipe = controller.GetVulkanPipelineState()
    cs = pipe.computeShader
    refl = cs.reflection
    result['cs_name'] = refl.entryPoint if refl else None
    result['disassembly'] = controller.DisassembleShader(pipe.compute.pipelineResourceId, refl, '')
    # Check data in rw[0] and rw[1]
    if rw:
        tiled_raw = controller.GetBufferData(rw[0].descriptor.resource, rw[0].descriptor.byteOffset, min(rw[0].descriptor.byteSize, 1024))
        result['tiled_len'] = len(tiled_raw)
        import struct
        words = [struct.unpack('<I', tiled_raw[i:i+4])[0] for i in range(0, min(len(tiled_raw), 64), 4)]
        result['tiled_first_words_hex'] = [f"0x{w:08x}" for w in words]
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'dispatch_10982.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
