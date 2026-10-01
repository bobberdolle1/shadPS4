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
    target_offset = 168493056
    sd = controller.GetStructuredFile()
    def get_val(node):
        if hasattr(node.data, 'basic'):
            b = node.data.basic
            for attr in ['u', 'i', 'f', 'b', 'c']:
                if hasattr(b, attr):
                    return getattr(b, attr)
        return node.AsString()
    matching_actions = []
    for a in flat:
        if a.flags & rd.ActionFlags.Copy:
            chunk = sd.chunks[a.events[-1].chunkIndex]
            if chunk.name == 'vkCmdCopyBuffer':
                pRegions = chunk.FindChild('pRegions')
                if pRegions:
                    for i in range(pRegions.NumChildren()):
                        el = pRegions.GetChild(i)
                        dst = get_val(el.FindChild('dstOffset'))
                        sz = get_val(el.FindChild('size'))
                        if isinstance(dst, int) and isinstance(sz, int):
                            if dst <= target_offset < dst + sz:
                                matching_actions.append({
                                    'event': a.eventId,
                                    'dstOffset': dst,
                                    'size': sz,
                                    'srcOffset': get_val(el.FindChild('srcOffset')),
                                    'srcBuffer': str(a.copySource),
                                    'dstBuffer': str(a.copyDestination),
                                })
    result['matching_actions'] = matching_actions
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'find_exact_copy_for_offset.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
