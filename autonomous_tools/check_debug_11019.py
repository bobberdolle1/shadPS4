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
    controller.SetFrameEvent(11019, True)
    pipe = controller.GetVulkanPipelineState()
    refl = pipe.fragmentShader.reflection
    result['ps_name'] = refl.entryPoint if refl else None
    result['debuggable'] = refl.debugInfo.debuggable if refl else None
    if refl and not refl.debugInfo.debuggable:
        result['debug_status'] = refl.debugInfo.debugStatus
    inputs = rd.DebugPixelInputs()
    inputs.primitive = 0
    trace = controller.DebugPixel(100, 650, inputs)
    result['trace_is_none'] = (trace is None)
    if trace:
        result['debugger_is_none'] = (trace.debugger is None)
        if trace.debugger:
            result['ok'] = True
            controller.FreeTrace(trace)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'debug_11019_status.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
