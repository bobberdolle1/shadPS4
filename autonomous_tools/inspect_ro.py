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
            path = root / f"sampled_ro_{str(desc.resource).replace('::','-')}.png"
            controller.SaveTexture(save, str(path))
            entry['saved'] = str(path)
        result['ro'].append(entry)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'sampled_common.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
