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
    src_buf_id = a10984.copySource
    controller.SetFrameEvent(10984, True)
    buf_data = controller.GetBufferData(src_buf_id, 0, 0)
    result['buffer_size'] = len(buf_data)
    import struct
    words = struct.unpack(f'<{min(len(buf_data)//2, 256)}H', buf_data[:min(len(buf_data)//2, 256)*2])
    first_few = [words[i:i+4] for i in range(0, min(len(words), 32), 4)]
    result['first_pixels_half'] = [list(p) for p in first_few]
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'buffer_590_data.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
