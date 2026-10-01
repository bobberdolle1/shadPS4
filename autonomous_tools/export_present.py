import json
import sys
from pathlib import Path
import renderdoc as rd

log_dir = Path(sys.argv[1])
meta = json.loads((log_dir / 'result.json').read_text())
cap = rd.OpenCaptureFile()
controller = None
saved = []
try:
    status = cap.OpenFile(meta['capture'], '', None)
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    resnames = {r.resourceId: r.name for r in controller.GetResources()}
    last_event = controller.GetRootActions()[-1].eventId
    controller.SetFrameEvent(last_event, True)
    for tex in controller.GetTextures():
        if tex.width == 1280 and tex.height == 720 and tex.format.Name() == 'B8G8R8A8_UNORM':
            name = resnames.get(tex.resourceId, str(tex.resourceId)).replace(':', '_').replace(' ', '_')
            path = log_dir / f'present_{name}.png'
            tex.Save(0, str(path))
            saved.append({'res': str(tex.resourceId), 'name': resnames.get(tex.resourceId),
                          'file': path.name})
except Exception as exc:
    saved.append({'error': str(exc)})
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
print(json.dumps(saved, indent=2))
sys.exit(0 if saved and 'error' not in saved[0] else 1)
