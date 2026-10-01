import json
import struct
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
    controller.SetFrameEvent(10984, True)

    resnames = {r.resourceId: r.name for r in controller.GetResources()}

    tex = [t for t in controller.GetTextures() if str(t.resourceId) == 'ResourceId::9707'][0]
    w, h = tex.width, tex.height
    result['tex'] = {'w': w, 'h': h, 'depth': tex.depth, 'fmt': str(tex.format.Name()),
                     'mips': tex.mips, 'arraysize': tex.arraysize,
                     'name': resnames.get(tex.resourceId)}
    data = controller.GetTextureData(tex.resourceId, rd.Subresource(0, 0, 0))
    result['tex_bytes'] = len(data)
    counts = {}
    row_nonzero = {}
    for y in range(h):
        base = y * w * 8
        nz = 0
        for x in range(w):
            off = base + x * 8
            vals = struct.unpack_from('<4H', data, off)
            counts[vals] = counts.get(vals, 0) + 1
            if vals != (0, 0, 0, 0):
                nz += 1
        if nz:
            row_nonzero[y] = nz
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
    result['tex_top_texel_values'] = [
        {'halves': list(k), 'count': v,
         'floats': list(struct.unpack('<4e', struct.pack('<4H', *k)))}
        for k, v in top
    ]
    result['tex_distinct_values'] = len(counts)
    result['tex_nonzero_rows'] = len(row_nonzero)
    rows = sorted(row_nonzero.items())
    result['tex_nonzero_row_range'] = [rows[0][0], rows[-1][0]] if rows else None

    buf = [b for b in controller.GetBuffers() if str(b.resourceId) == 'ResourceId::590'][0]
    result['buf_len'] = buf.length
    result['buf_name'] = resnames.get(buf.resourceId)
    probe = 1 << 20
    first = controller.GetBufferData(buf.resourceId, 0, probe)
    pat = bytes.fromhex('e632d75ce632d75c')
    mismatch = None
    for i in range(0, probe - 8, 8):
        if first[i:i + 8] != pat:
            mismatch = i
            break
    result['buf_first_mismatch'] = mismatch
    if mismatch is not None:
        result['buf_at_mismatch'] = first[mismatch:mismatch + 48].hex()
    result['buf_first_64'] = first[:64].hex()
    deep = {}
    for off in (0, 1 << 16, 1 << 18, (1 << 20) - 64, 4 << 20, 8 << 20, 15 << 20):
        if off + 64 <= buf.length:
            deep[str(off)] = controller.GetBufferData(buf.resourceId, off, 64).hex()
    result['buf_deep'] = deep
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'tex9707_analysis.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
