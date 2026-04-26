import sys, json
from graphify.build import build_from_json
from graphify.cluster import score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.report import generate
from pathlib import Path

extraction = json.loads(Path('.graphify_extract.json').read_text(encoding='utf-8-sig'))
detection  = json.loads(Path('.graphify_detect.json').read_text(encoding='utf-8-sig'))
analysis   = json.loads(Path('.graphify_analysis.json').read_text(encoding='utf-8-sig'))

G = build_from_json(extraction)
communities = {int(k): v for k, v in analysis['communities'].items()}
cohesion = {int(k): v for k, v in analysis['cohesion'].items()}

labels = {
    0: "Memory Management System",
    1: "Agent Core & Initialization",
    2: "System Control Tools",
    3: "Project Roadmap & Vision",
    4: "Interaction & Learning Logic",
    5: "Automation Stack",
    6: "Voice Interface"
}

questions = suggest_questions(G, communities, labels)
report = generate(G, communities, cohesion, labels, analysis['gods'], analysis['surprises'], detection, {}, '.', suggested_questions=questions)
Path('graphify-out/GRAPH_REPORT.md').write_text(report, encoding='utf-8')
Path('.graphify_labels.json').write_text(json.dumps({str(k): v for k, v in labels.items()}))
print('Report updated with community labels')
