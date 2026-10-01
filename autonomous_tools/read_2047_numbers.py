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
    flat = []
    def walk(actions):
        for action in actions:
            flat.append(action)
            walk(action.children)
    walk(controller.GetRootActions())
    a2047 = [a for a in flat if a.eventId == 2047][0]
    sd = controller.GetStructuredFile()
    chunk = sd.chunks[a2047.events[-1].chunkIndex]
    def get_val(node):
        if hasattr(node.data, 'basic'):
            b = node.data.basic
            # check members of basic
            for attr in ['u', 'i', 'f', 'b', 'c']:
                if hasattr(b, attr):
                    return getattr(b, attr)
        return node.AsString()
    regions = []
    pRegions = chunk.FindChild('pRegions')
    for i in range(pRegions.NumChildren()):
        el = pRegions.GetChild(i)
        regions.append({
            'srcOffset': get_val(el.FindChild('srcOffset')),
            'dstOffset': get_val(el.FindChild('dstOffset')),
            'size': get_val(el.FindChild('size')),
        })
    result['regions'] = regions
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'chunk_2047_numbers.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
