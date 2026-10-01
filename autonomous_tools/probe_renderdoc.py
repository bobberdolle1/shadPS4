import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import REPO  # noqa: E402
import renderdoc as rd

result = {
    'version': rd.GetVersionString(),
    'execute': rd.ExecuteAndInject.__doc__,
    'control_pid': rd.TargetControl.GetPID.__doc__,
    'result': rd.ExecuteResult.__doc__,
}
Path(str(REPO / 'autonomous_tools/renderdoc-api.json')).write_text(json.dumps(result, indent=2))
sys.exit(0)
