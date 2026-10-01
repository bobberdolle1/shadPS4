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
    cpipe = controller.GetPipelineState()
    ro = cpipe.GetReadOnlyResources(rd.ShaderStage.Pixel, False)
    tex_res_id = ro[0].descriptor.resource
    result['sampled_res_id'] = str(tex_res_id)
    sub = rd.Subresource()
    history = controller.PixelHistory(tex_res_id, 100, 650, sub, rd.CompType.Typeless)
    result['history'] = []
    for mod in history:
        result['history'].append({
            'event': mod.eventId,
            'passed': mod.Passed(),
            'pre': list(mod.preMod.col.floatValue),
            'post': list(mod.postMod.col.floatValue),
            'out': list(mod.shaderOut.col.floatValue) if mod.shaderOut.IsValid() else None,
            'prim': mod.primitiveID,
        })
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'trace_fsr_output.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
