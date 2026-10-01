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
    controller.SetFrameEvent(11019, True)
    pipe = controller.GetVulkanPipelineState()
    ds = pipe.graphics.descriptorSets[0]
    result['layout'] = str(ds.layoutResourceId)
    ssbo_binding = pipe.graphics.descriptorBuffers if hasattr(pipe.graphics, 'descriptorBuffers') else None
    result['has_desc_buffers'] = bool(ssbo_binding)
    result['desc_set_res'] = str(ds.descriptorSetResourceId)
    # Check if we can read the dynamic offsets or bindings via reflection
    refl = pipe.fragmentShader.reflection
    cb_refl = refl.constantBlocks
    result['cb_refl'] = [{'name': c.name, 'byteSize': c.byteSize, 'bind': c.bindPoint} for c in cb_refl]
    ro_refl = refl.readOnlyResources
    result['ro_refl'] = [{'name': r.name, 'bind': r.bindPoint} for r in ro_refl]
    rw_refl = refl.readWriteResources
    result['rw_refl'] = [{'name': r.name, 'bind': r.bindPoint} for r in rw_refl]
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'draw_11019_bindings_map.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
