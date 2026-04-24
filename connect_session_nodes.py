import json
import networkx as nx

# Load the graph with database relationships
with open('graphify-out/graph_fully_connected.json', 'r') as f:
    graph_data = json.load(f)

# Create NetworkX graph to analyze connectivity
G = nx.Graph()
for link in graph_data['links']:
    G.add_edge(link['_src'], link['_tgt'])

# Find connected components
components = list(nx.connected_components(G))
print(f"Total components before bridging: {len(components)}")

# Get component assignments for each node
node_to_component = {}
for i, component in enumerate(components):
    for node_id in component:
        node_to_component[node_id] = i

# Find nodes in the main component (component 0)
main_component_nodes = set(components[0])

# Find all isolated nodes (single-node components)
isolated_nodes = []
for i, component in enumerate(components):
    if len(component) == 1:
        node_id = list(component)[0]
        node = next((n for n in graph_data['nodes'] if n['id'] == node_id), None)
        if node and node['community'] >= 200:  # Session/memory nodes
            isolated_nodes.append(node)

print(f"Found {len(isolated_nodes)} isolated session nodes")

# Create bridging connections for isolated session nodes
new_links = []

# Find main component nodes related to sessions/memory
session_bridge_targets = []
for node_id in main_component_nodes:
    node = next((n for n in graph_data['nodes'] if n['id'] == node_id), None)
    if node:
        node_label_lower = node['label'].lower()
        if any(keyword in node_label_lower for keyword in ['session', 'memory', 'chat', 'message', 'task', 'learning']):
            session_bridge_targets.append(node_id)

print(f"Found {len(session_bridge_targets)} session-related bridge targets")

# Connect each isolated session node to a bridge target
for isolated_node in isolated_nodes:
    # Find a suitable bridge target (prefer ones with similar channel type)
    bridge_target = session_bridge_targets[0]  # Default to first

    # Try to match by channel type if possible
    node_label = isolated_node['label'].lower()
    if 'chat' in node_label and len(session_bridge_targets) > 1:
        # Look for chat-related bridge
        for target_id in session_bridge_targets[1:]:
            target_node = next((n for n in graph_data['nodes'] if n['id'] == target_id), None)
            if target_node and 'chat' in target_node['label'].lower():
                bridge_target = target_id
                break

    new_links.append({
        '_src': isolated_node['id'],
        '_tgt': bridge_target,
        'relation': 'session_bridge',
        'weight': 0.3
    })

# Add the new links
graph_data['links'].extend(new_links)

print(f"Added {len(new_links)} session bridging connections")

# Save the fully connected graph
with open('graphify-out/graph_completely_connected.json', 'w') as f:
    json.dump(graph_data, f, indent=2)

print(f"Saved completely connected graph with {len(graph_data['nodes'])} nodes and {len(graph_data['links'])} links")