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
    flat = []

    def walk(actions):
        for action in actions:
            flat.append(action)
            walk(action.children)
    walk(controller.GetRootActions())
    a10984 = [a for a in flat if a.eventId == 10984][0]
    sd = controller.GetStructuredFile()

    def val(node):
        try:
            b = node.data.basic
            for attr in ('u', 'i', 'f', 'b'):
                if hasattr(b, attr):
                    return getattr(b, attr)
        except Exception:
            pass
        try:
            return node.AsString()
        except Exception:
            return None

    chunk = sd.chunks[a10984.events[-1].chunkIndex]
    result['chunk'] = chunk.name
    params = {}
    for i in range(chunk.NumChildren()):
        child = chunk.GetChild(i)
        params[child.name] = None
    result['param_names'] = list(params.keys())

    def serialize(node):
        d = {'name': node.name}
        if node.NumChildren() > 0:
            d['children'] = [serialize(node.GetChild(i)) for i in range(node.NumChildren())]
        else:
            d['v'] = val(node)
        return d

    result['structured'] = serialize(chunk)

    # Also dump image 9707 details and the source buffer name
    tex = [t for t in controller.GetTextures() if str(t.resourceId) == 'ResourceId::9707'][0]
    result['tex_9707'] = {
        'name': tex.name,
        'type': str(tex.type),
        'dims': [tex.dimensions[0], tex.dimensions[1], tex.dimensions[2], tex.dimensions[3]],
        'format': str(tex.format.Name()),
        'mips': tex.mipLevels,
        'arraysize': tex.arraySize,
        'samples': tex.samples,
    }
    buf = [b for b in controller.GetBuffers() if str(b.resourceId) == 'ResourceId::590'][0]
    result['buf_590'] = {'name': buf.name, 'length': buf.length}
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'copy_10984_regions.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
