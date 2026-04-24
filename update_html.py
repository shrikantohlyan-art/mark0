import json
import re

# Load the connected graph data
with open('graphify-out/graph_connected.json', 'r') as f:
    data = json.load(f)

# Load the HTML template
with open('graphify-out/graph.html', 'r') as f:
    html_content = f.read()

# Prepare the data for embedding
nodes = []
for node in data['nodes']:
    node_data = {
        "id": node['id'],
        "label": node.get('label', node['id']),
        "color": {
            "background": "#4E79A7",  # Default color
            "border": "#4E79A7",
            "highlight": {"background": "#ffffff", "border": "#4E79A7"}
        },
        "size": 10.0,
        "font": {"size": 0, "color": "#ffffff"},
        "title": node.get('label', node['id']),
        "community": node.get('community', 0),
        "community_name": f"Community {node.get('community', 0)}",
        "source_file": node.get('source_file', ''),
        "file_type": node.get('file_type', 'code'),
        "degree": 1  # Will be calculated
    }
    nodes.append(node_data)

edges = []
for link in data['links']:
    edge_data = {
        "from": link['_src'],
        "to": link['_tgt'],
        "weight": link.get('weight', 1.0)
    }
    edges.append(edge_data)

# Calculate degrees
degree_map = {}
for edge in edges:
    degree_map[edge['from']] = degree_map.get(edge['from'], 0) + 1
    degree_map[edge['to']] = degree_map.get(edge['to'], 0) + 1

for node in nodes:
    node['degree'] = degree_map.get(node['id'], 0)
    node['size'] = 10.0 + min(node['degree'] * 0.5, 10.0)  # Scale size by degree

# Create legend
communities = {}
for node in data['nodes']:
    comm_id = node.get('community', 0)
    if comm_id not in communities:
        communities[comm_id] = {'count': 0, 'color': '#4E79A7'}  # Default color
    communities[comm_id]['count'] += 1

legend = []
for comm_id, info in communities.items():
    legend.append({
        'cid': comm_id,
        'label': f'Community {comm_id}',
        'color': info['color'],
        'count': info['count']
    })

# Update HTML content
html_content = re.sub(
    r'const RAW_NODES = \[.*?\];',
    f'const RAW_NODES = {json.dumps(nodes)};',
    html_content,
    flags=re.DOTALL
)

html_content = re.sub(
    r'const RAW_EDGES = \[.*?\];',
    f'const RAW_EDGES = {json.dumps(edges)};',
    html_content,
    flags=re.DOTALL
)

html_content = re.sub(
    r'const LEGEND = \[.*?\];',
    f'const LEGEND = {json.dumps(legend)};',
    html_content,
    flags=re.DOTALL
)

# Update stats
stats_text = f'{len(nodes)} nodes &middot; {len(edges)} edges &middot; {len(communities)} communities'
html_content = re.sub(
    r'<div id="stats">.*?</div>',
    f'<div id="stats">{stats_text}</div>',
    html_content
)

# Save updated HTML
with open('graphify-out/graph_connected.html', 'w') as f:
    f.write(html_content)

print("Updated HTML saved to graphify-out/graph_connected.html")
print(f"Nodes: {len(nodes)}, Edges: {len(edges)}, Communities: {len(communities)}")