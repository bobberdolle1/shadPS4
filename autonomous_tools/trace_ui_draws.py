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
    events = [11019, 11025]
    for ev in events:
        controller.SetFrameEvent(ev, True)
        pipe = controller.GetVulkanPipelineState()
        refl = pipe.fragmentShader.reflection
        cpipe = controller.GetPipelineState()
        ro = cpipe.GetReadOnlyResources(rd.ShaderStage.Pixel, False)
        entry = {
            'disassembly': controller.DisassembleShader(pipe.graphics.pipelineResourceId, refl, ''),
            'ro': [{'res': str(u.descriptor.resource), 'view': str(u.descriptor.view), 'fmt': u.descriptor.format.Name()} for u in ro]
        }
        for u in ro:
            if u.descriptor.resource != rd.ResourceId():
                save = rd.TextureSave()
                save.resourceId = u.descriptor.resource
                save.destType = rd.FileType.PNG
                save.alpha = rd.AlphaMapping.Preserve
                path = root / f"input_to_{ev}_{str(u.descriptor.resource).replace('::','-')}.png"
                controller.SaveTexture(save, str(path))
                entry['saved_texture'] = str(path)
        result[str(ev)] = entry
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'draws_11019_11025.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
