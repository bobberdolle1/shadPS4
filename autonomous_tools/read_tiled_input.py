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
    controller.SetFrameEvent(10982, True)
    cpipe = controller.GetPipelineState()
    rw = cpipe.GetReadWriteResources(rd.ShaderStage.Compute, False)
    tiled_res = rw[0].descriptor.resource
    tiled_offset = rw[0].descriptor.byteOffset
    tiled_size = rw[0].descriptor.byteSize
    raw = controller.GetBufferData(tiled_res, tiled_offset, tiled_size)
    result['tiled_size'] = len(raw)
    needle = b'\xe6\x32\xd7\x5c'
    idx = raw.find(needle)
    result['needle_in_tiled_buffer'] = idx
    # Count non-zero dwords
    import struct
    dwords = struct.unpack(f'<{len(raw)//4}I', raw)
    non_zero = sum(1 for d in dwords if d != 0)
    result['non_zero_dwords'] = non_zero
    result['total_dwords'] = len(dwords)
    # Find first non-zero dword
    for i, d in enumerate(dwords):
        if d != 0:
            result['first_non_zero_idx'] = i
            result['first_non_zero_val'] = f"0x{d:08x}"
            break
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'check_tiled_input_10982.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
