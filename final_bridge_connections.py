import json
import networkx as nx

# Load the graph
with open('graphify-out/graph_completely_connected.json', 'r') as f:
    graph_data = json.load(f)

# Create NetworkX graph to find isolated nodes
G = nx.Graph()
for link in graph_data['links']:
    G.add_edge(link['_src'], link['_tgt'])

# Find all components
components = list(nx.connected_components(G))

# Get main component
main_component = max(components, key=len)
main_component_set = set(main_component)

# Find all isolated nodes (single-node components)
isolated_nodes = []
for component in components:
    if len(component) == 1:
        node_id = list(component)[0]
        isolated_nodes.append(node_id)

print(f"Found {len(isolated_nodes)} isolated nodes")

# Find bridge targets in main component
bridge_targets = []
for node_id in main_component:
    node = next((n for n in graph_data['nodes'] if n['id'] == node_id), None)
    if node:
        label_lower = node['label'].lower()
        if any(keyword in label_lower for keyword in ['session', 'memory', 'chat', 'message', 'task', 'learning', 'os', 'action', 'tool']):
            bridge_targets.append(node_id)

print(f"Found {len(bridge_targets)} bridge targets in main component")

# Add connections for isolated nodes
new_links = []
for i, isolated_node_id in enumerate(isolated_nodes):
    # Connect to a bridge target (cycle through them)
    bridge_target = bridge_targets[i % len(bridge_targets)]
    new_links.append({
        '_src': isolated_node_id,
        '_tgt': bridge_target,
        'relation': 'isolated_bridge',
        'weight': 0.2
    })

# Add the new links
graph_data['links'].extend(new_links)

print(f"Added {len(new_links)} connections for isolated nodes")

# Save the final connected graph
with open('graphify-out/graph_final_connected.json', 'w') as f:
    json.dump(graph_data, f, indent=2)

print(f"Saved final connected graph with {len(graph_data['nodes'])} nodes and {len(graph_data['links'])} links")