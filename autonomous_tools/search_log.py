import re
from pathlib import Path

log = Path('E:/programming/shadPS4/autonomous_logs/xhigh-renderdoc-title-65s/shad_log.txt')
found = []
with log.open('r', encoding='utf-8', errors='replace') as f:
    for line in f:
        if '100a0b0000' in line or '100a0b' in line:
            found.append(line.strip())
print(f"Found {len(found)} lines:")
for l in found[:20]:
    print(l)
