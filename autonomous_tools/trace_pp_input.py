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
    controller.SetFrameEvent(11035, True)
    pipe = controller.GetPipelineState()
    ro = pipe.GetReadOnlyResources(rd.ShaderStage.Pixel, False)
    result['ro_count'] = len(ro)
    result['ro'] = []
    for u in ro:
        desc = u.descriptor
        entry = {
            'res_id': str(desc.resource),
            'view_id': str(desc.view),
            'format': desc.format.Name(),
            'type': str(desc.type),
        }
        if desc.resource != rd.ResourceId():
            save = rd.TextureSave()
            save.resourceId = desc.resource
            save.destType = rd.FileType.PNG
            save.alpha = rd.AlphaMapping.Preserve
            path = root / f"input_to_pp_pass_{str(desc.resource).replace('::','-')}.png"
            controller.SaveTexture(save, str(path))
            entry['saved'] = str(path)
        result['ro'].append(entry)
    source_tex_id = ro[0].descriptor.resource
    sub = rd.Subresource()
    history = controller.PixelHistory(source_tex_id, 100, 650, sub, rd.CompType.Typeless)
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
    result['source_pixel_history'] = items
    if items:
        source_event = items[-1]['event']
        controller.SetFrameEvent(source_event, True)
        source_pipe = controller.GetVulkanPipelineState()
        result['source_event'] = source_event
        result['source_pipeline'] = str(source_pipe.graphics.pipelineResourceId)
        ps = source_pipe.fragmentShader
        result['source_pixel_shader'] = str(ps.resourceId)
        refl = ps.reflection
        if refl:
            result['source_ps_name'] = refl.entryPoint
            result['source_debuggable'] = refl.debugInfo.debuggable
            result['source_disassembly'] = controller.DisassembleShader(source_pipe.graphics.pipelineResourceId, refl, '')
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'trace_input_pp_pass.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
