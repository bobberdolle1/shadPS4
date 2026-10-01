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
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    if status != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    res599 = [t for t in controller.GetTextures() if str(t.resourceId) == 'ResourceId::599'][0].resourceId
    pts = {
        'bar_bottom_left': (300, 967),
        'green_rect_subtitle': (1050, 900),
        'bar_under_logo': (195, 292),
        'reference_bg': (900, 300),
    }
    result['histories'] = {}
    for name, (x, y) in pts.items():
        sub = rd.Subresource()
        try:
            history = controller.PixelHistory(res599, x, y, sub, rd.CompType.Typeless)
        except Exception as exc:
            result['histories'][name] = {'error': str(exc)}
            continue
        items = []
        for mod in history:
            items.append({
                'event': mod.eventId,
                'passed': mod.Passed(),
                'pre': list(mod.preMod.col.floatValue),
                'post': list(mod.postMod.col.floatValue),
                'shader_out': list(mod.shaderOut.col.floatValue) if mod.shaderOut.IsValid() else None,
                'primitive': mod.primitiveID,
            })
        result['histories'][name] = items
    # Name the last (topmost) event per point
    result['top_events'] = {}
    for name, items in result['histories'].items():
        if isinstance(items, list) and items:
            last = max(items, key=lambda d: d['event'])
            e = last['event']
            controller.SetFrameEvent(e, True)
            sd = controller.GetStructuredFile()
            act = [a for a in controller.GetRootActions()]
            flat = []

            def walk(acts):
                for a in acts:
                    flat.append(a)
                    walk(a.children)
            walk(act)
            match = [a for a in flat if a.eventId == e]
            result['top_events'][name] = {
                'event': e,
                'name': match[0].GetName(sd) if match else None,
                'flags': str(match[0].flags) if match else None,
            }
except Exception as exc:
    result['error'] = str(exc)
finally:
    if controller is not None:
        controller.Shutdown()
    cap.Shutdown()
    (root / 'green_hist_599.json').write_text(json.dumps(result, indent=2))
sys.exit(0 if 'error' not in result else 1)
