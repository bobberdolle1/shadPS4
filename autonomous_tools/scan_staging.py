import json
import os
import struct
from pathlib import Path
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
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    resnames = {r.resourceId: r.name for r in controller.GetResources()}
    pat = b'\xe6\x32\xd7\x5c'
    target = struct.unpack('<I', pat)[0]
    # Detiler staging blocks are DeviceLocal StreamBuffers.
    staging = [b for b in controller.GetBuffers()
               if 'StreamBuffer(DeviceLocal)' in (resnames.get(b.resourceId) or '')]
    result['staging_count'] = len(staging)
    out = []
    for buf in staging:
        data = controller.GetBufferData(buf.resourceId, 0, buf.length)
        count = 0
        first = None
        for i in range(0, len(data) - 3, 4):
            if data[i:i + 4] == pat:
                count += 1
                if first is None:
                    first = i
        out.append({'id': str(buf.resourceId), 'name': resnames.get(buf.resourceId),
                    'len': buf.length, 'pattern_words': count, 'first_at': first})
    result['staging'] = out
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'staging_pattern_scan.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
