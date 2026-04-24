import json
import networkx as nx
from collections import defaultdict

# Load the graph (try connected version first, then original)
try:
    with open('graphify-out/graph_connected.json', 'r') as f:
        data = json.load(f)
    print("Loading previously connected graph")
except FileNotFoundError:
    with open('graphify-out/graph.json', 'r') as f:
        data = json.load(f)
    print("Loading original graph")

# Create NetworkX graph
G = nx.Graph()

# Add nodes
for node in data['nodes']:
    G.add_node(node['id'], **node)

# Add edges
for link in data['links']:
    G.add_edge(link['_src'], link['_tgt'], **link)

# Get connected components
components = list(nx.connected_components(G))
largest_comp = max(components, key=len)
isolated_nodes = [list(comp)[0] for comp in components if len(comp) == 1]

print(f"Found {len(components)} components, {len(isolated_nodes)} isolated nodes")

# Create a mapping of node labels to IDs for easier lookup
label_to_ids = defaultdict(list)
for node in data['nodes']:
    label = node.get('label', '').lower().strip()
    if label:
        label_to_ids[label].append(node['id'])

# Function to find best match in largest component
def find_best_match(isolated_node_id, largest_comp_ids):
    isolated_node = G.nodes[isolated_node_id]
    isolated_label = isolated_node.get('label', '').lower()
    isolated_file = isolated_node.get('source_file', '')
    
    # First, try exact label match
    for node_id in largest_comp_ids:
        if G.nodes[node_id].get('label', '').lower() == isolated_label:
            return node_id
    
    # Then try file-based connections
    if isolated_file:
        for node_id in largest_comp_ids:
            if G.nodes[node_id].get('source_file', '') == isolated_file:
                return node_id
    
    # Finally, try keyword matching
    isolated_words = set(isolated_label.split())
    best_match = None
    best_score = 0
    for node_id in largest_comp_ids:
        node_label = G.nodes[node_id].get('label', '').lower()
        node_words = set(node_label.split())
        score = len(isolated_words & node_words)
        if score > best_score:
            best_score = score
            best_match = node_id
    
    return best_match

# Connect ALL remaining components to the largest one
remaining_components = [comp for comp in components if comp != largest_comp]
added_edges = 0
for comp in remaining_components:
    # Find a representative node from this component
    comp_node = list(comp)[0]
    target_id = find_best_match(comp_node, largest_comp)
    if target_id:
        new_edge = {
            "relation": "connects_component",
            "confidence": "INFERRED",
            "source_file": "component_connection",
            "source_location": "L1",
            "weight": 0.4,
            "_src": comp_node,
            "_tgt": target_id,
            "source": comp_node,
            "target": target_id,
            "confidence_score": 0.4
        }
        data['links'].append(new_edge)
        added_edges += 1
        print(f"Connected component ({len(comp)} nodes) via {comp_node} to {target_id}")
    else:
        # If no good match, connect to a central node
        central_node = list(largest_comp)[0]  # Just pick first node
        new_edge = {
            "relation": "connects_component",
            "confidence": "INFERRED",
            "source_file": "component_connection",
            "source_location": "L1",
            "weight": 0.3,
            "_src": comp_node,
            "_tgt": central_node,
            "source": comp_node,
            "target": central_node,
            "confidence_score": 0.3
        }
        data['links'].append(new_edge)
        added_edges += 1
        print(f"Connected component ({len(comp)} nodes) via {comp_node} to central node {central_node}")

# Save the updated graph
with open('graphify-out/graph_connected.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Added {added_edges} edges to connect the graph")
print(f"Updated graph saved to graphify-out/graph_connected.json")

# Verify connectivity
G2 = nx.Graph()
for node in data['nodes']:
    G2.add_node(node['id'])
for link in data['links']:
    G2.add_edge(link['_src'], link['_tgt'])

components_after = list(nx.connected_components(G2))
print(f"Components after: {len(components_after)}")
print(f"Largest component size: {max(len(c) for c in components_after)}")
print(f"Graph is now connected: {nx.is_connected(G2)}")

# Show remaining components
if len(components_after) > 1:
    print("Remaining components:")
    for i, comp in enumerate(sorted(components_after, key=len, reverse=True)[:5]):
        comp_nodes = list(comp)
        labels = [G2.nodes[n].get('label', n) for n in comp_nodes[:3]]
        print(f"  Component {i}: {len(comp)} nodes - {labels}")