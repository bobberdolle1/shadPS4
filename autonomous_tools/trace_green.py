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
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    tex_170 = [t for t in controller.GetTextures() if str(t.resourceId) == 'ResourceId::170'][0]
    sub = rd.Subresource()
    history = controller.PixelHistory(tex_170.resourceId, 100, 650, sub, rd.CompType.Typeless)
    items = []
    for mod in history:
        items.append({
            'event': mod.eventId,
            'passed': mod.Passed(),
            'pre': list(mod.preMod.col.floatValue),
            'post': list(mod.postMod.col.floatValue),
            'shader_out': list(mod.shaderOut.col.floatValue) if mod.shaderOut.IsValid() else None,
            'primitive': mod.primitiveID,
        })
    result['pixel_100_650'] = items
    if items:
        last_event = items[-1]['event']
        controller.SetFrameEvent(last_event, True)
        pipe = controller.GetVulkanPipelineState()
        result['event'] = last_event
        result['pipeline'] = str(pipe.graphics.pipelineResourceId)
        ps = pipe.fragmentShader
        result['pixel_shader'] = str(ps.resourceId)
        refl = ps.reflection
        if refl:
            result['ps_name'] = refl.entryPoint
            result['debuggable'] = refl.debugInfo.debuggable
            result['ro_resources'] = [{'name': r.name, 'bind': r.bindPoint, 'type': str(r.resType)} for r in refl.readOnlyResources]
            result['cbuffers'] = [{'name': cb.name, 'bind': cb.bindPoint, 'size': cb.byteSize} for cb in refl.constantBlocks]
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'green_pixel_history.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
