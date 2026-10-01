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
    controller.SetFrameEvent(1941, True)
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
    flat = []
    def walk(actions):
        for action in actions:
            flat.append(action)
            walk(action.children)
    walk(controller.GetRootActions())
    a1941 = [a for a in flat if a.eventId == 1941][0]
    result['dim'] = list(a1941.dispatchDimension)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'dispatch_1941.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
