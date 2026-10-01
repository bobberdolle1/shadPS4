import json
from pathlib import Path
import struct
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
    sd = controller.GetStructuredFile()
    resnames = {r.resourceId: r.name for r in controller.GetResources()}

    pushes = [a for a in flat if 10960 <= a.eventId <= 10983
              and 'PushDescriptorSet' in a.GetName(sd)]
    result['push_events'] = [a.eventId for a in pushes]

    def val(node):
        try:
            b = node.data.basic
            for attr in ('u', 'i', 'f', 'b'):
                if hasattr(b, attr):
                    return getattr(b, attr)
        except Exception:
            pass
        return None

    details = []
    for a in pushes:
        chunk = sd.chunks[a.events[-1].chunkIndex]
        binds = []
        for i in range(chunk.NumChildren()):
            c = chunk.GetChild(i)
            if c.Name().endswith('pDescriptorWrites') or c.name == 'pDescriptorWrites':
                for j in range(c.NumChildren()):
                    w = c.GetChild(j)
                    rec = {'name': w.name}
                    for k in range(w.NumChildren()):
                        f = w.GetChild(k)
                        if f.name == 'pBufferInfo' and f.NumChildren() > 0:
                            bi = f.GetChild(0)
                            for m in range(bi.NumChildren()):
                                g = bi.GetChild(m)
                                if g.name == 'buffer':
                                    rec['buffer'] = str(val(g))
                                    rec['buffer_name'] = resnames.get(val(g))
                                elif g.name == 'offset':
                                    rec['offset'] = val(g)
                                elif g.name == 'range':
                                    rec['range'] = val(g)
                        elif f.name == 'dstBinding':
                            rec['binding'] = val(f)
                        elif f.name == 'descriptorType':
                            rec['type'] = val(f)
                    binds.append(rec)
        details.append({'event': a.eventId, 'binds': binds})
    result['push_details'] = details

    # Read the tiled source buffer referenced by binding 0 of the last push
    tiled = None
    for d in details:
        for b in d['binds']:
            if b.get('binding') == 0 and 'buffer_name' in b:
                tiled = b
    if tiled is not None and tiled.get('buffer_name'):
        rid = [r.resourceId for r in controller.GetBuffers()
               if str(r.resourceId) == tiled['buffer']]
        if rid:
            controller.SetFrameEvent(10982, True)
            buf = [b for b in controller.GetBuffers() if str(b.resourceId) == tiled['buffer']][0]
            base = tiled.get('offset', 0)
            probe = 1 << 20
            data = controller.GetBufferData(buf.resourceId, base, probe)
            pat = bytes.fromhex('e632d75c')
            mismatch = None
            for i in range(0, probe - 8, 8):
                if data[i:i + 8] != pat + pat[:0] + data[i + 4:i + 8] and data[i:i + 4] != pat:
                    mismatch = i
                    break
            result['tiled_source'] = {
                'buffer': tiled['buffer'], 'name': tiled['buffer_name'],
                'offset': base, 'first_mismatch_vs_pattern': mismatch,
                'first_64': data[:64].hex(),
            }
            # word histogram of first 256 KB
            hist = {}
            for i in range(0, 256 * 1024, 4):
                w = int.from_bytes(data[i:i + 4], 'little')
                hist[w] = hist.get(w, 0) + 1
            top = sorted(hist.items(), key=lambda kv: -kv[1])[:6]
            result['tiled_source']['top_words_256k'] = [
                {'word': f'0x{k:08x}', 'count': v} for k, v in top]
            result['tiled_source']['distinct_words_256k'] = len(hist)
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'detile_push_descriptors.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
