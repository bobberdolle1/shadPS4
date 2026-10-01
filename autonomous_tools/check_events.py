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
    events = [11034, 11035, 11036]
    for ev in events:
        try:
            controller.SetFrameEvent(ev, True)
            cpipe = controller.GetPipelineState()
            ro = cpipe.GetReadOnlyResources(rd.ShaderStage.Pixel, False)
            outs = cpipe.GetOutputTargets()
            result[str(ev)] = {
                'ro': [{'res': str(u.descriptor.resource), 'view': str(u.descriptor.view), 'fmt': u.descriptor.format.Name()} for u in ro],
                'outputs': [{'res': str(o.resource), 'view': str(o.view), 'fmt': o.format.Name()} for o in outs],
            }
        except Exception as e:
            result[str(ev)] = {'error': str(e)}
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'events_around_11035.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
