import json
import os
import sys
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import REPO  # noqa: E402
import renderdoc as rd

root = Path(os.environ.get('SCAN_DIR',
                           str(REPO / 'autonomous_logs/xhigh-renderdoc-title-65s')))
meta = json.loads((root / 'result.json').read_text())
cap = rd.OpenCaptureFile()
controller = None
result = {}
try:
    status = cap.OpenFile(meta['capture'], '', None)
    status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    controller.SetFrameEvent(10983, True)
    pat = bytes.fromhex('e632d75c')
    target = 0x5CD732E6

    hits = []
    scanned = 0
    for buf in controller.GetBuffers():
        if buf.length > (32 << 20):
            continue
        scanned += 1
        try:
            data = controller.GetBufferData(buf.resourceId, 0, buf.length)
        except Exception as exc:
            hits.append({'id': str(buf.resourceId), 'error': str(exc)})
            continue
        count = 0
        first = None
        step = 4
        for i in range(0, len(data) - 3, step):
            if data[i:i + 4] == pat:
                count += 1
                if first is None:
                    first = i
        if count:
            hits.append({'id': str(buf.resourceId), 'len': buf.length, 'pat_words': count,
                         'first_at': first})
    result['buffers_scanned'] = scanned
    result['buffers_with_pattern'] = sorted(hits, key=lambda h: -h.get('pat_words', 0))
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'pattern_scan.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
