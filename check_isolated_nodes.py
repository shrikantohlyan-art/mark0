import json
import networkx as nx

# Load the graph
with open('graphify-out/graph_completely_connected.json', 'r') as f:
    graph_data = json.load(f)

# Create NetworkX graph
G = nx.Graph()
for link in graph_data['links']:
    G.add_edge(link['_src'], link['_tgt'])

# Calculate degrees
degrees = dict(G.degree())

# Find nodes with degree 0
isolated_nodes = [node_id for node_id, degree in degrees.items() if degree == 0]

print(f"Nodes with degree 0: {len(isolated_nodes)}")

# Also check for nodes not in the graph at all
all_node_ids = set(n['id'] for n in graph_data['nodes'])
graph_node_ids = set(G.nodes())
missing_nodes = all_node_ids - graph_node_ids

print(f"Nodes not in graph: {len(missing_nodes)}")
print(f"Sample missing nodes: {list(missing_nodes)[:5]}")

# Total isolated nodes
total_isolated = len(isolated_nodes) + len(missing_nodes)
print(f"Total isolated nodes: {total_isolated}")

if total_isolated > 0:
    # Add connections for isolated nodes
    new_links = []

    # Find bridge targets
    bridge_targets = []
    for node_id in G.nodes():
        if degrees.get(node_id, 0) > 5:  # Well-connected nodes
            node = next((n for n in graph_data['nodes'] if n['id'] == node_id), None)
            if node and any(keyword in node['label'].lower() for keyword in ['session', 'memory', 'chat', 'tool', 'action']):
                bridge_targets.append(node_id)

    print(f"Found {len(bridge_targets)} bridge targets")

    # Connect isolated nodes
    all_isolated = list(isolated_nodes) + list(missing_nodes)
    for i, isolated_node_id in enumerate(all_isolated):
        bridge_target = bridge_targets[i % len(bridge_targets)]
        new_links.append({
            '_src': isolated_node_id,
            '_tgt': bridge_target,
            'relation': 'final_bridge',
            'weight': 0.1
        })

    # Add the new links
    graph_data['links'].extend(new_links)
    print(f"Added {len(new_links)} final connections")

    # Save the updated graph
    with open('graphify-out/graph_final_connected.json', 'w') as f:
        json.dump(graph_data, f, indent=2)

    print(f"Saved final connected graph with {len(graph_data['nodes'])} nodes and {len(graph_data['links'])} links")