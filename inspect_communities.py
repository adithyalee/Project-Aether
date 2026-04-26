import json
from pathlib import Path
analysis = json.loads(Path('.graphify_analysis.json').read_text(encoding='utf-8-sig'))
extraction = json.loads(Path('.graphify_extract.json').read_text(encoding='utf-8-sig'))
node_map = {n['id']: n['label'] for n in extraction['nodes']}
for cid, nodes in analysis['communities'].items():
    print(f"Community {cid}: {[node_map.get(nid, nid) for nid in nodes[:10]]}")
