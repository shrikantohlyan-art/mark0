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
main_component_nodes = components[0]

# Find database nodes that are not in the main component
database_nodes = []
for node in graph_data['nodes']:
    if node['community'] >= 100 and node['id'] not in main_component_nodes:
        database_nodes.append(node)

print(f"Database nodes not in main component: {len(database_nodes)}")

# Create bridging connections
new_links = []

# Connect customer/service nodes to relevant code nodes
customer_related_keywords = ['customer', 'client', 'user', 'contact', 'phone', 'email', 'service']
for db_node in database_nodes:
    node_label_lower = db_node['label'].lower()

    # Find potential bridge nodes in main component
    bridge_candidates = []
    for main_node_id in main_component_nodes:
        main_node = next((n for n in graph_data['nodes'] if n['id'] == main_node_id), None)
        if main_node and any(keyword in main_node['label'].lower() for keyword in customer_related_keywords):
            bridge_candidates.append(main_node_id)

    # Connect to up to 3 bridge candidates
    for bridge_id in bridge_candidates[:3]:
        new_links.append({
            '_src': db_node['id'],
            '_tgt': bridge_id,
            'relation': 'database_bridge',
            'weight': 0.6
        })

# Connect session/memory nodes to relevant code nodes
session_related_keywords = ['session', 'memory', 'message', 'task', 'model', 'provider', 'learning']
for db_node in database_nodes:
    if db_node['community'] >= 200:  # Session/memory nodes
        node_label_lower = db_node['label'].lower()

        # Find potential bridge nodes in main component
        bridge_candidates = []
        for main_node_id in main_component_nodes:
            main_node = next((n for n in graph_data['nodes'] if n['id'] == main_node_id), None)
            if main_node and any(keyword in main_node['label'].lower() for keyword in session_related_keywords):
                bridge_candidates.append(main_node_id)

        # Connect to up to 2 bridge candidates
        for bridge_id in bridge_candidates[:2]:
            new_links.append({
                '_src': db_node['id'],
                '_tgt': bridge_id,
                'relation': 'memory_bridge',
                'weight': 0.5
            })

# Add the new links
graph_data['links'].extend(new_links)

print(f"Added {len(new_links)} bridging connections")

# Save the fully connected graph
with open('graphify-out/graph_fully_connected.json', 'w') as f:
    json.dump(graph_data, f, indent=2)

print(f"Saved fully connected graph with {len(graph_data['nodes'])} nodes and {len(graph_data['links'])} links")