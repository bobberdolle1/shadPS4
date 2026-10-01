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
    target_599 = [t for t in controller.GetTextures() if str(t.resourceId) == 'ResourceId::599'][0]
    tex_278 = [t for t in controller.GetTextures() if str(t.resourceId) == 'ResourceId::278'][0]
    controller.SetFrameEvent(11034, True)
    save = rd.TextureSave()
    save.resourceId = target_599.resourceId
    save.destType = rd.FileType.PNG
    save.alpha = rd.AlphaMapping.Preserve
    controller.SaveTexture(save, str(root / 'res_599_at_11034.png'))
    save.resourceId = tex_278.resourceId
    controller.SaveTexture(save, str(root / 'res_278_at_11034.png'))
    controller.SetFrameEvent(11035, True)
    save.resourceId = tex_278.resourceId
    controller.SaveTexture(save, str(root / 'res_278_at_11035.png'))
    result['done'] = True
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'save_steps.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
