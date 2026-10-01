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
    controller.SetFrameEvent(1973, True)
    pipe = controller.GetVulkanPipelineState()
    cs = pipe.computeShader
    refl = cs.reflection
    result['cs_name'] = refl.entryPoint if refl else None
    result['disassembly'] = controller.DisassembleShader(pipe.compute.pipelineResourceId, refl, '')
    cpipe = controller.GetPipelineState()
    ro = cpipe.GetReadOnlyResources(rd.ShaderStage.Compute, False)
    cb = cpipe.GetConstantBlocks(rd.ShaderStage.Compute, False)
    rw = cpipe.GetReadWriteResources(rd.ShaderStage.Compute, False)
    result['ro'] = [{'res': str(u.descriptor.resource), 'offset': u.descriptor.byteOffset, 'size': u.descriptor.byteSize, 'format': u.descriptor.format.Name()} for u in ro]
    result['cb'] = [{'res': str(u.descriptor.resource), 'offset': u.descriptor.byteOffset, 'size': u.descriptor.byteSize} for u in cb]
    result['rw'] = [{'res': str(u.descriptor.resource), 'offset': u.descriptor.byteOffset, 'size': u.descriptor.byteSize, 'format': u.descriptor.format.Name(), 'type': str(u.descriptor.type)} for u in rw]
    flat = []
    def walk(actions):
        for action in actions:
            flat.append(action)
            walk(action.children)
    walk(controller.GetRootActions())
    a1973 = [a for a in flat if a.eventId == 1973][0]
    result['dim'] = list(a1973.dispatchDimension)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'dispatch_1973_details.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
