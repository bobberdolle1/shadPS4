import ctypes
import json
import os
from pathlib import Path
import shutil
import sys
import time
import renderdoc as rd

# Paths come from paths.py so this script is not tied to one machine's drive layout.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import EXE, GAME_EBOOT, REPO as root  # noqa: E402
out = root / 'autonomous_logs/xhigh-verify-clean-65s'
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)
mods = []
for name, value in [('VK_ADD_IMPLICIT_LAYER_PATH', str(root / 'autonomous_tools/RenderDoc_1.46_64')),
                    ('ENABLE_VULKAN_RENDERDOC_CAPTURE', '1')]:
    mods.append(rd.EnvironmentModification(rd.EnvMod.Set, rd.EnvSep.NoSep, name, value))
result = rd.ExecuteAndInject(str(EXE), str(root),
                             f'-g {GAME_EBOOT} -f false',
                             mods, str(out / 'probe'), rd.CaptureOptions(), False)
info = {'version': rd.GetVersionString(), 'launch_result': str(result.result), 'ident': result.ident,
        'messages': []}
control = None
process = None
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
kernel.OpenProcess.restype = ctypes.c_void_p
kernel.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
kernel.CloseHandle.argtypes = [ctypes.c_void_p]
try:
    if not result.ident:
        raise RuntimeError(str(result.result))
    control = rd.CreateTargetControl('', result.ident, 'MFG verify', False)
    if control is None:
        raise RuntimeError('Cannot connect to injected emulator')
    info['pid'] = control.GetPID()
    process = kernel.OpenProcess(1, False, info['pid'])
    start = time.monotonic()
    triggered = False
    while time.monotonic() - start < 200 and control.Connected():
        message = control.ReceiveMessage(None)
        if not triggered and time.monotonic() - start >= 65:
            control.TriggerCapture(1)
            triggered = True
            info['messages'].append({'event': 'trigger',
                                     'elapsed': time.monotonic() - start,
                                     'api': control.GetAPI()})
        if message.type == rd.TargetControlMessageType.NewCapture:
            info['capture'] = message.newCapture.path
            info['frame'] = message.newCapture.frameNumber
            break
    info['observed_seconds'] = time.monotonic() - start
except Exception as exc:
    info['error'] = str(exc)
finally:
    if control is not None:
        control.Shutdown()
    if process:
        kernel.TerminateProcess(process, 0)
        kernel.CloseHandle(process)
    app_log = Path(os.environ['APPDATA']) / 'shadPS4/log/shad_log.txt'
    if app_log.exists():
        shutil.copy2(app_log, out / 'shad_log.txt')
    (out / 'result.json').write_text(json.dumps(info, indent=2))
sys.exit(0 if 'capture' in info else 1)
