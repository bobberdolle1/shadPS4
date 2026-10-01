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
    controller.SetFrameEvent(11508, True)
    pipe = controller.GetVulkanPipelineState()
    ds = pipe.graphics.descriptorSets[0]
    result['desc_set'] = str(ds.descriptorSetResourceId)
    b0 = ds.bindings[0]
    result['binding0'] = {
        'type': str(b0.type),
        'binds': [{'image_view': str(bind.viewResourceId), 'sampler': str(bind.samplerResourceId), 'layout': str(bind.imageLayout)} for bind in b0.binds]
    }
    view_id = b0.binds[0].viewResourceId
    views = [v for v in controller.GetResources() if v.resourceId == view_id]
    result['view_name'] = views[0].name if views else None
    tex = controller.GetTexture(view_id)
    if tex:
        result['texture'] = {
            'id': str(tex.resourceId),
            'w': tex.width,
            'h': tex.height,
            'format': tex.format.Name(),
        }
        save = rd.TextureSave()
        save.resourceId = tex.resourceId
        save.destType = rd.FileType.PNG
        save.alpha = rd.AlphaMapping.Preserve
        path = root / 'sampled_texture_11508.png'
        controller.SaveTexture(save, str(path))
        result['saved_texture'] = str(path)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'sampled_11508.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
