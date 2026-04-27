import json
from graphify.detect import detect
from pathlib import Path

result = detect(Path('D:/Project Aether'))
out = json.dumps(result, indent=2)
Path('graphify-out/.graphify_detect.json').write_text(out, encoding='utf-8')
print(out[:500])
