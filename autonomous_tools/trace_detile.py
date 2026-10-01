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

    resnames = {r.resourceId: r.name for r in controller.GetResources()}
    buf590 = [b for b in controller.GetBuffers() if str(b.resourceId) == 'ResourceId::590'][0]

    # Find every action before 10984 that writes ResourceId::590
    writers = []
    for a in flat:
        if a.eventId >= 10984:
            continue
        outs = [str(o) for o in a.outputs]
        if str(buf590.resourceId) in outs:
            writers.append({
                'event': a.eventId,
                'name': a.GetName(controller.GetStructuredFile()),
                'flags': str(a.flags),
                'outputs': outs,
            })
    result['writers_of_590_before_10984'] = writers[-12:]

    # Also: which actions read from 590 before 10984
    readers = []
    for a in flat:
        if a.eventId >= 10984:
            continue
        ins = [str(i) for i in a.inputs]
        if str(buf590.resourceId) in ins:
            readers.append({'event': a.eventId,
                            'name': a.GetName(controller.GetStructuredFile())})
    result['readers_of_590_before_10984'] = readers[-12:]

    # Detail of the last few writers: read pipeline state descriptors
    detail = []
    for w in writers[-4:]:
        e = w['event']
        controller.SetFrameEvent(e, True)
        cpipe = controller.GetPipelineState()
        entry = {'event': e, 'name': w['name']}
        entry['ssbo'] = [{'res': str(u.descriptor.resource),
                          'offset': u.descriptor.byteOffset,
                          'size': u.descriptor.byteSize,
                          'resname': resnames.get(u.descriptor.resource)}
                         for u in cpipe.GetReadOnlyStorageResources(rd.ShaderStage.Compute, False)]
        entry['ubo'] = [{'res': str(u.descriptor.resource),
                         'offset': u.descriptor.byteOffset,
                         'size': u.descriptor.byteSize,
                         'resname': resnames.get(u.descriptor.resource)}
                        for u in cpipe.GetConstantBlocks(rd.ShaderStage.Compute, False)]
        entry['cshaders'] = [{'res': str(u.descriptor.resource),
                              'offset': u.descriptor.byteOffset,
                              'size': u.descriptor.byteSize,
                              'resname': resnames.get(u.descriptor.resource)}
                             for u in cpipe.GetReadWriteStorageResources(rd.ShaderStage.Compute, False)]
        detail.append(entry)
    result['writer_detail'] = detail
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'detile_trace.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
