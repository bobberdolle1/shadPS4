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
    controller.SetFrameEvent(1973, True)
    cpipe = controller.GetPipelineState()
    rw = cpipe.GetReadWriteResources(rd.ShaderStage.Compute, False)
    cb = cpipe.GetConstantBlocks(rd.ShaderStage.Compute, False)
    pipe = controller.GetVulkanPipelineState()
    pc = pipe.pushconsts
    import struct
    pc_words = [struct.unpack('<I', pc[i:i+4])[0] for i in range(0, len(pc), 4)]
    result['pc_words'] = [hex(w) for w in pc_words]
    # In cs_1973, push_data.buf_offsets0.x was used:
    # buf0_off = BitFieldUExtract(x, 0, 8)
    # buf1_off = BitFieldUExtract(x, 8, 8)
    buf_offsets0_x = pc_words[4] # offset 16 is index 4
    result['buf_offsets0_x'] = hex(buf_offsets0_x)
    buf0_off = buf_offsets0_x & 0xff
    buf1_off = (buf_offsets0_x >> 8) & 0xff
    result['buf0_off'] = buf0_off
    result['buf1_off'] = buf1_off
    # Now check srt_flatbuf (binding 2 in descriptor set 0)
    # and ssbo_1 (binding 0)
    # and ssbo_2 (binding 1)
    # Read the data for ssbo_1 (rw[0])
    raw_ssbo1 = controller.GetBufferData(rw[0].descriptor.resource, rw[0].descriptor.byteOffset, rw[0].descriptor.byteSize)
    ssbo1_words = [struct.unpack('<I', raw_ssbo1[i:i+4])[0] for i in range(0, len(raw_ssbo1), 4)]
    result['ssbo1_words_hex'] = [hex(w) for w in ssbo1_words]
    # Check srt_flatbuf
    # srt_flatbuf is binding 2
    # rw[2] or ro
    if len(rw) > 2:
        raw_srt = controller.GetBufferData(rw[2].descriptor.resource, rw[2].descriptor.byteOffset, min(rw[2].descriptor.byteSize, 64))
        srt_words = [struct.unpack('<I', raw_srt[i:i+4])[0] for i in range(0, len(raw_srt), 4)]
        result['srt_words_hex'] = [hex(w) for w in srt_words]
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'cs_1973_constants.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
