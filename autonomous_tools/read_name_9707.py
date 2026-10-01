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
    controller.SetFrameEvent(10984, True)
    pipe = controller.GetVulkanPipelineState()
    tex_9707 = [t for t in controller.GetTextures() if str(t.resourceId) == 'ResourceId::9707'][0]
    names = {r.resourceId: r.name for r in controller.GetResources()}
    result['name'] = names.get(tex_9707.resourceId)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'name_9707.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
