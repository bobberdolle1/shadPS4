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
    controller.SetFrameEvent(11019, True)
    cpipe = controller.GetPipelineState()
    ro = cpipe.GetReadOnlyResources(rd.ShaderStage.Pixel, False)
    tex_res = ro[0].descriptor.resource
    tex = [t for t in controller.GetTextures() if t.resourceId == tex_res][0]
    tex_data = controller.GetTextureData(tex_res, rd.Subresource())
    result['tex_bytes'] = len(tex_data)
    import struct
    hwords = struct.unpack(f'<{len(tex_data)//2}H', tex_data)
    coords = [(20, 20), (200, 200), (500, 100), (770, 192), (800, 200)]
    samples = []
    for x, y in coords:
        idx = y * tex.width + x
        h = hwords[idx*4 : idx*4 + 4]
        f = [struct.unpack('<e', struct.pack('<H', val))[0] for val in h]
        samples.append({'x': x, 'y': y, 'half': list(h), 'float': f})
    result['samples'] = samples
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'sampled_tex_pixels.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
