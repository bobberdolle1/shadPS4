import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import REPO  # noqa: E402

root = REPO / 'autonomous_logs' / 'xhigh-renderdoc-title-65s'
data = json.loads((root / 'dispatch_1973_details.json').read_text())
dis = data.get('disassembly', '')
Path(root / 'cs_1973_disasm.txt').write_text(dis, encoding='utf-8')
print(f"Wrote {len(dis)} characters to cs_1973_disasm.txt")
