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
    refl = pipe.fragmentShader.reflection
    result['pipeline'] = str(pipe.graphics.pipelineResourceId)
    result['shader'] = str(pipe.fragmentShader.resourceId)
    result['disassembly'] = controller.DisassembleShader(pipe.graphics.pipelineResourceId, refl, '')
    inputs = rd.DebugPixelInputs()
    inputs.primitive = 1
    trace = controller.DebugPixel(100, 650, inputs)
    if trace.debugger:
        states = []
        while True:
            more = controller.ContinueDebug(trace.debugger)
            if not more:
                break
            states.extend(more)
        result['steps'] = len(states)
        result['last_instruction'] = states[-1].nextInstruction if states else None
        changes = []
        for s in states:
            for ch in s.changes:
                changes.append({'step': s.stepIndex, 'inst': s.nextInstruction, 'before': ch.before.name, 'after': ch.after.name, 'value': list(ch.after.value.f32v[0:4]) if ch.after.value else None})
        result['changes'] = changes
        controller.FreeTrace(trace)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'debug_11508.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
