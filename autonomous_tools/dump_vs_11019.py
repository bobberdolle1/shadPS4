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
    vs = pipe.vertexShader
    refl = vs.reflection
    dis = controller.DisassembleShader(pipe.graphics.pipelineResourceId, refl, '')
    Path(root / 'shader_11019_vs_disasm.txt').write_text(dis, encoding='utf-8')
    result['disasm_length'] = len(dis)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'dump_vs_11019.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
