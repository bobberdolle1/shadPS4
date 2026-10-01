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
    sd = controller.GetStructuredFile()
    first_copy = None
    for chunk in sd.chunks:
        if chunk.name == 'vkCmdCopyBuffer':
            first_copy = chunk
            break
    if first_copy:
        result['chunk_members'] = dir(first_copy)
        result['num_children'] = first_copy.NumChildren()
        params = []
        for i in range(first_copy.NumChildren()):
            c = first_copy.GetChild(i)
            params.append({'name': c.name, 'str': str(c.data.str if hasattr(c.data, 'str') else c.data.basic)})
        result['params'] = params
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'dump_copy_chunk.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
