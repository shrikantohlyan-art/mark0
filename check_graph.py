import json

data = json.load(open('graphify-out/graph_completely_connected.json'))
print(f'Nodes: {len(data["nodes"])}, Links: {len(data["links"])}')
print('Last 5 links:')
for l in data['links'][-5:]:
    print(f'{l["_src"]} -> {l["_tgt"]} ({l.get("relation", "-")})')

# Check if session nodes exist
session_nodes = [n for n in data['nodes'] if n['community'] >= 200]
print(f'Session nodes: {len(session_nodes)}')
print('Sample session nodes:')
for n in session_nodes[:3]:
    print(f'  {n["id"]}: {n["label"]}')