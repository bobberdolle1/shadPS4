import json
from pathlib import Path

root = Path('E:/programming/shadPS4/autonomous_logs/xhigh-renderdoc-title-65s')
data = json.loads((root / 'dispatch_1973_details.json').read_text())
dis = data.get('disassembly', '')
Path(root / 'cs_1973_disasm.txt').write_text(dis, encoding='utf-8')
print(f"Wrote {len(dis)} characters to cs_1973_disasm.txt")
