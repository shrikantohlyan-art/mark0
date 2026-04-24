import json
import networkx as nx

# Load the graph with database relationships
with open('graphify-out/graph_connected_with_db.json', 'r') as f:
    graph_data = json.load(f)

# Create NetworkX graph to analyze connectivity
G = nx.Graph()
for link in graph_data['links']:
    G.add_edge(link['_src'], link['_tgt'])

# Find connected components
components = list(nx.connected_components(G))
print(f"Total components: {len(components)}")

# Get component assignments for each node
node_to_component = {}
for i, component in enumerate(components):
    for node_id in component:
        node_to_component[node_id] = i

# Find nodes in the main component (component 0)
main_component_nodes = set(components[0])

# Find database nodes that are not in the main component
database_nodes = []
for node in graph_data['nodes']:
    if node['community'] >= 100 and node['id'] not in main_component_nodes:
        database_nodes.append(node)

print(f"Database nodes not in main component: {len(database_nodes)}")

# Create bridging connections - simpler approach
new_links = []

# Connect each database component to the main component via a few key bridge nodes
bridge_targets = [
    'customer', 'user', 'session', 'memory', 'database', 'learning', 'task', 'model'
]

# Find main component nodes that match bridge targets
bridge_nodes = []
for node_id in main_component_nodes:
    node = next((n for n in graph_data['nodes'] if n['id'] == node_id), None)
    if node:
        node_label_lower = node['label'].lower()
        if any(target in node_label_lower for target in bridge_targets):
            bridge_nodes.append(node_id)

print(f"Found {len(bridge_nodes)} potential bridge nodes in main component")

# For each database component, connect a few nodes to bridge targets
connected_components = set()
for db_node in database_nodes[:20]:  # Limit connections
    if db_node['id'] not in node_to_component:
        print(f"Warning: Node {db_node['id']} not found in components")
        continue

    component_id = node_to_component[db_node['id']]
    if component_id in connected_components:
        continue

    # Connect this component to 2 bridge nodes
    for bridge_id in bridge_nodes[:2]:
        new_links.append({
            '_src': db_node['id'],
            '_tgt': bridge_id,
            'relation': 'database_bridge',
            'weight': 0.4
        })

    connected_components.add(component_id)

# Add the new links
graph_data['links'].extend(new_links)

print(f"Added {len(new_links)} bridging connections")

# Save the fully connected graph
with open('graphify-out/graph_fully_connected.json', 'w') as f:
    json.dump(graph_data, f, indent=2)

print(f"Saved fully connected graph with {len(graph_data['nodes'])} nodes and {len(graph_data['links'])} links")