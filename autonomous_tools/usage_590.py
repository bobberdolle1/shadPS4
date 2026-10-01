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
    flat = []

    def walk(actions):
        for action in actions:
            flat.append(action)
            walk(action.children)
    walk(controller.GetRootActions())
    by_id = {a.eventId: a for a in flat}
    sd = controller.GetStructuredFile()

    for rid_str in ('ResourceId::590', 'ResourceId::9707'):
        rid = [b.resourceId for b in controller.GetBuffers()
               if str(b.resourceId) == rid_str]
        if not rid:
            continue
        usage = controller.GetResourceUsage(rid[0])
        entries = []
        for rng in usage.ranges:
            for e in rng.events:
                a = by_id.get(e.eventId)
                entries.append({
                    'event': e.eventId,
                    'name': a.GetName(sd) if a else None,
                    'flags': str(a.flags) if a else None,
                })
        result[rid_str] = entries[-25:]

    # Inspect the last dispatch that touched 590
    disp = [v for k, vs in result.items() if k == 'ResourceId::590' for v in vs
            if v['flags'] and 'Dispatch' in v['flags']]
    result['last_dispatch_writing_590'] = disp[-1] if disp else None
    if disp:
        e = disp[-1]['event']
        controller.SetFrameEvent(e, True)
        cpipe = controller.GetPipelineState()
        resnames = {r.resourceId: r.name for r in controller.GetResources()}
        binds = []
        for i in range(3):
            for stage in (rd.ShaderStage.Compute,):
                for u in cpipe.GetReadWriteStorageResources(stage, False):
                    if i == 1 and u.dstBinding == 1:
                        binds.append({'binding': 1, 'res': str(u.descriptor.resource),
                                      'offset': u.descriptor.byteOffset,
                                      'size': u.descriptor.byteSize,
                                      'name': resnames.get(u.descriptor.resource)})
                for u in cpipe.GetReadOnlyStorageResources(stage, False):
                    binds.append({'binding': u.dstBinding, 'res': str(u.descriptor.resource),
                                  'offset': u.descriptor.byteOffset,
                                  'size': u.descriptor.byteSize,
                                  'name': resnames.get(u.descriptor.resource)})
                for u in cpipe.GetConstantBlocks(stage, False):
                    binds.append({'binding': u.dstBinding, 'res': str(u.descriptor.resource),
                                  'offset': u.descriptor.byteOffset,
                                  'size': u.descriptor.byteSize,
                                  'name': resnames.get(u.descriptor.resource)})
        result['detile_binds'] = binds
        pipe = controller.GetVulkanPipelineState()
        refl = pipe.computeShader.reflection
        result['cs_entry'] = refl.entryPoint if refl else None
        if refl:
            result['disasm'] = controller.DisassembleShader(
                pipe.compute.pipelineResourceId, refl, '')
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'buf590_usage.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
