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
    controller.SetFrameEvent(10984, True)
    buf590 = [b for b in controller.GetBuffers() if str(b.resourceId) == 'ResourceId::590'][0]
    result['len'] = buf590.length
    result['name'] = buf590.name

    # Look at the constant pattern extent
    probe = 1 << 20
    first = controller.GetBufferData(buf590.resourceId, 0, probe)
    result['first_1mb_hex'] = first[:64].hex()
    # find first offset where the 8-byte pattern stops repeating
    pat = bytes.fromhex('e632d75ce632d75c')
    mismatch = None
    for i in range(0, probe - 8, 8):
        if first[i:i + 8] != pat:
            mismatch = i
            break
    result['first_mismatch_within_1mb'] = mismatch
    if mismatch is not None:
        result['at_mismatch_hex'] = first[mismatch:mismatch + 64].hex()

    # Row structure: pitch is 2048 texels * 8 bytes = 16384 bytes
    rows = []
    for r in range(0, 8):
        off = r * 16384
        rows.append({'row': r, 'hex': first[off:off + 32].hex()})
    result['first_rows'] = rows

    # Check some offsets deeper in the buffer for real data
    samples = {}
    for off in (0, 1 << 16, 1 << 18, 1 << 20, 4 << 20, 8 << 20, 12 << 20, (1 << 24) - 64):
        if off + 64 <= buf590.length:
            samples[str(off)] = controller.GetBufferData(buf590.resourceId, off, 64).hex()
    result['deep_samples'] = samples
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'buf590_map.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
