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

    resnames = {r.resourceId: r.name for r in controller.GetResources()}
    target = 'ResourceId::590'

    hits = []
    for a in flat:
        if a.eventId >= 10984:
            break
        if not (a.flags & rd.ActionFlags.Dispatch):
            continue
        controller.SetFrameEvent(a.eventId, True)
        try:
            cpipe = controller.GetPipelineState()
            rw = cpipe.GetReadWriteStorageResources(rd.ShaderStage.Compute, False)
        except Exception:
            continue
        names = [(str(u.descriptor.resource), resnames.get(u.descriptor.resource)) for u in rw]
        if any(n[0] == target for n in names):
            hits.append({'event': a.eventId, 'rw': names})

    result['dispatches_writing_590'] = hits[-6:]
    if hits:
        e = hits[-1]['event']
        controller.SetFrameEvent(e, True)
        cpipe = controller.GetPipelineState()
        rw = cpipe.GetReadWriteStorageResources(rd.ShaderStage.Compute, False)
        ro = cpipe.GetReadOnlyStorageResources(rd.ShaderStage.Compute, False)
        ubo = cpipe.GetConstantBlocks(rd.ShaderStage.Compute, False)
        result['event'] = e
        result['rw_detail'] = [{'res': str(u.descriptor.resource),
                                'offset': u.descriptor.byteOffset,
                                'size': u.descriptor.byteSize,
                                'name': resnames.get(u.descriptor.resource)} for u in rw]
        result['ro_detail'] = [{'res': str(u.descriptor.resource),
                                'offset': u.descriptor.byteOffset,
                                'size': u.descriptor.byteSize,
                                'name': resnames.get(u.descriptor.resource)} for u in ro]
        result['ubo_detail'] = [{'res': str(u.descriptor.resource),
                                 'offset': u.descriptor.byteOffset,
                                 'size': u.descriptor.byteSize,
                                 'name': resnames.get(u.descriptor.resource)} for u in ubo]
        pipe = controller.GetVulkanPipelineState()
        refl = pipe.computeShader.reflection
        result['cs_entry'] = refl.entryPoint if refl else None
        result['disasm'] = controller.DisassembleShader(
            pipe.compute.pipelineResourceId, refl, '') if refl else ''
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'detile_dispatch.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
