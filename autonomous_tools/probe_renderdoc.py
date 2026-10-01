import json
from pathlib import Path
import sys
import renderdoc as rd

result = {
    'version': rd.GetVersionString(),
    'execute': rd.ExecuteAndInject.__doc__,
    'control_pid': rd.TargetControl.GetPID.__doc__,
    'result': rd.ExecuteResult.__doc__,
}
Path('E:/programming/shadPS4/autonomous_tools/renderdoc-api.json').write_text(json.dumps(result, indent=2))
sys.exit(0)
