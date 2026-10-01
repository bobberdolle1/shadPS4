import json
from pathlib import Path
import sys
import renderdoc as rd

root = Path('E:/programming/shadPS4/autonomous_logs/xhigh-renderdoc-title')
meta = json.loads((root / 'result.json').read_text())
cap = rd.OpenCaptureFile()
controller = None
result = {}
try:
    status = cap.OpenFile(meta['capture'], '', None)
    result['open_file'] = str(status)
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    result['replay'] = str(status)
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    resources = {r.resourceId: r.name for r in controller.GetResources()}
    flat = []
    def walk(actions):
        for action in actions:
            flat.append(action)
            walk(action.children)
    walk(controller.GetRootActions())
    result['actions'] = [{'event': a.eventId, 'name': a.GetName(controller.GetStructuredFile()), 'flags': str(a.flags), 'outputs': [str(r) for r in a.outputs], 'copy_destination': str(a.copyDestination)} for a in flat]
    last = max(a.eventId for a in flat)
    controller.SetFrameEvent(last, True)
    textures = controller.GetTextures()
    result['textures'] = [{'id': str(t.resourceId), 'name': resources.get(t.resourceId), 'width': t.width, 'height': t.height, 'mips': t.mips, 'arraysize': t.arraysize, 'format': t.format.Name(), 'flags': str(t.creationFlags)} for t in textures]
    save_ids = {a.copyDestination for a in flat if a.flags & rd.ActionFlags.Present}
    result['exports'] = []
    for texture in textures:
        if texture.resourceId not in save_ids:
            continue
        save = rd.TextureSave()
        save.resourceId = texture.resourceId
        save.destType = rd.FileType.PNG
        save.alpha = rd.AlphaMapping.Preserve
        save.slice.sliceIndex = 0
        path = root / ('present-' + str(texture.resourceId).replace('::', '-') + '.png')
        status = controller.SaveTexture(save, str(path))
        result['exports'].append({'id': str(texture.resourceId), 'path': str(path), 'result': str(status)})
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'analysis.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
