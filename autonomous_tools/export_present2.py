import json
import sys
from pathlib import Path
import renderdoc as rd

log_dir = Path(sys.argv[1])
meta = json.loads((log_dir / 'result.json').read_text())
cap = rd.OpenCaptureFile()
controller = None
out = []
try:
    status = cap.OpenFile(meta['capture'], '', None)
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    cands = [t for t in controller.GetTextures()
             if t.width == 1280 and t.height == 720
             and 'B8G8R8A8' in t.format.Name()]
    out.append({'candidates': [(str(t.resourceId), t.format.Name()) for t in cands]})
    if cands:
        tex = cands[0]
        path = log_dir / 'present_after_fix.png'
        tex.Save(0, str(path))
        out.append({'saved': str(path)})
except Exception as exc:
    out.append({'error': str(exc)})
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
print(json.dumps(out, indent=2))
sys.exit(0 if out and 'error' not in out[-1] else 1)
