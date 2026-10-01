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
    controller.SetFrameEvent(10451, True)
    pipe = controller.GetVulkanPipelineState()
    refl = pipe.fragmentShader.reflection
    result['ro'] = [{'name': r.name, 'bind': r.bindArraySize} for r in refl.readOnlyResources]
    save_dir = root / 'draw_10451_textures'
    save_dir.mkdir(exist_ok=True)
    cpipe = controller.GetPipelineState()
    ro = cpipe.GetReadOnlyResources(rd.ShaderStage.Pixel, False)
    result['bound_ro'] = []
    for idx, u in enumerate(ro):
        desc = u.descriptor
        entry = {'idx': idx, 'res_id': str(desc.resource), 'format': desc.format.Name(), 'type': str(desc.type)}
        if desc.resource != rd.ResourceId():
            save = rd.TextureSave()
            save.resourceId = desc.resource
            save.destType = rd.FileType.PNG
            save.alpha = rd.AlphaMapping.Preserve
            path = save_dir / f"tex_{idx}_{str(desc.resource).replace('::','-')}.png"
            controller.SaveTexture(save, str(path))
            entry['path'] = str(path)
        result['bound_ro'].append(entry)
    result['disassembly'] = controller.DisassembleShader(pipe.graphics.pipelineResourceId, refl, '')
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'draw_10451_info.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
