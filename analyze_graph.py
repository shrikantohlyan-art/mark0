import json
import networkx as nx
from collections import defaultdict

# Load the graph
with open('graphify-out/graph_final_connected.json', 'r') as f:
    data = json.load(f)

# Create NetworkX graph
G = nx.Graph()

# Add nodes
for node in data['nodes']:
    G.add_node(node['id'], **node)

# Add edges
for link in data['links']:
    G.add_edge(link['_src'], link['_tgt'], **link)

# Analyze connectivity
components = list(nx.connected_components(G))
print(f"Number of connected components: {len(components)}")
print(f"Largest component size: {max(len(c) for c in components)}")
print(f"Smallest component size: {min(len(c) for c in components)}")

# Find isolated nodes
isolated = list(nx.isolates(G))
print(f"Number of isolated nodes: {len(isolated)}")

# Get component details
component_details = []
for i, comp in enumerate(components):
    nodes_in_comp = list(comp)
    communities_in_comp = set(G.nodes[n]['community'] for n in nodes_in_comp if 'community' in G.nodes[n])
    labels = [G.nodes[n].get('label', n) for n in nodes_in_comp[:3]]  # First 3 labels
    component_details.append({
        'id': i,
        'size': len(comp),
        'communities': communities_in_comp,
        'sample_labels': labels
    })

# Sort by size descending
component_details.sort(key=lambda x: x['size'], reverse=True)

print("\nComponent details (sorted by size):")
for comp in component_details[:10]:  # Show top 10
    print(f"Component {comp['id']}: {comp['size']} nodes, communities: {sorted(comp['communities'])}, samples: {comp['sample_labels']}")

# Find potential bridges - nodes that could connect components
# Look for nodes with similar labels across components
node_labels = {}
for node_id, node_data in G.nodes(data=True):
    label = node_data.get('label', '').lower()
    if label:
        if label not in node_labels:
            node_labels[label] = []
        node_labels[label].append(node_id)

print("\nPotential bridge opportunities (same labels in different components):")
bridge_candidates = []
for label, node_ids in node_labels.items():
    if len(node_ids) > 1:
        components_for_label = set()
        for nid in node_ids:
            comp_id = None
            for i, comp in enumerate(components):
                if nid in comp:
                    comp_id = i
                    break
            if comp_id is not None:
                components_for_label.add(comp_id)
        
        if len(components_for_label) > 1:
            bridge_candidates.append({
                'label': label,
                'components': sorted(components_for_label),
                'nodes': node_ids
            })

# Sort by number of components connected
bridge_candidates.sort(key=lambda x: len(x['components']), reverse=True)

for bc in bridge_candidates[:20]:  # Show top 20
    print(f"'{bc['label']}': connects components {bc['components']} (nodes: {len(bc['nodes'])})")

# Suggest connections to make graph connected
print("\nSuggested connections to connect components:")
# Use a simple approach: connect each small component to the largest one
largest_comp = component_details[0]['id']
suggested_edges = []

for comp in component_details[1:]:  # Skip the largest
    if comp['size'] == 1:
        # For isolated nodes, find a similar node in the largest component
        isolated_node = list(components[comp['id']])[0]
        isolated_label = G.nodes[isolated_node].get('label', '').lower()
        
        # Find similar nodes in largest component
        candidates = []
        for node in components[largest_comp]:
            if G.nodes[node].get('label', '').lower() == isolated_label:
                candidates.append(node)
        
        if candidates:
            suggested_edges.append((isolated_node, candidates[0], 'same_label'))
        else:
            # Find any node with similar words
            isolated_words = set(isolated_label.split())
            best_match = None
            best_score = 0
            for node in components[largest_comp]:
                node_label = G.nodes[node].get('label', '').lower()
                node_words = set(node_label.split())
                score = len(isolated_words & node_words)
                if score > best_score:
                    best_score = score
                    best_match = node
            if best_match:
                suggested_edges.append((isolated_node, best_match, 'similar_words'))

print(f"Suggested {len(suggested_edges)} edges to connect isolated nodes:")
for src, tgt, reason in suggested_edges:
    src_label = G.nodes[src].get('label', src)
    tgt_label = G.nodes[tgt].get('label', tgt)
    print(f"  {src_label} --({reason})--> {tgt_label}")