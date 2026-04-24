import json

# Load the final connected graph data
with open('graphify-out/graph_final_connected.json', 'r') as f:
    data = json.load(f)

# Create the final comprehensive HTML file
html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Final Connected Knowledge Graph - Jarvis</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0f0f1a; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; display: flex; height: 100vh; overflow: hidden; }
  #graph { flex: 1; }
  #sidebar { width: 300px; background: #1a1a2e; border-left: 1px solid #2a2a4e; display: flex; flex-direction: column; overflow: hidden; }
  #search-wrap { padding: 12px; border-bottom: 1px solid #2a2a4e; }
  #search { width: 100%; background: #0f0f1a; border: 1px solid #3a3a5e; color: #e0e0e0; padding: 7px 10px; border-radius: 6px; font-size: 13px; outline: none; }
  #search:focus { border-color: #4E79A7; }
  #search-results { max-height: 140px; overflow-y: auto; padding: 4px 12px; border-bottom: 1px solid #2a2a4e; display: none; }
  .search-item { padding: 4px 6px; cursor: pointer; border-radius: 4px; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .search-item:hover { background: #2a2a4e; }
  #info-panel { padding: 14px; border-bottom: 1px solid #2a2a4e; min-height: 140px; }
  #info-panel h3 { font-size: 13px; color: #aaa; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
  #info-content { font-size: 13px; color: #ccc; line-height: 1.6; }
  #info-content .field { margin-bottom: 5px; }
  #info-content .field b { color: #e0e0e0; }
  #info-content .empty { color: #555; font-style: italic; }
  .neighbor-link { display: block; padding: 2px 6px; margin: 2px 0; border-radius: 3px; cursor: pointer; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; border-left: 3px solid #333; }
  .neighbor-link:hover { background: #2a2a4e; }
  #neighbors-list { max-height: 160px; overflow-y: auto; margin-top: 4px; }
  #legend-wrap { flex: 1; overflow-y: auto; padding: 12px; }
  #legend-wrap h3 { font-size: 13px; color: #aaa; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.05em; }
  .legend-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; cursor: pointer; border-radius: 4px; font-size: 12px; }
  .legend-item:hover { background: #2a2a4e; padding-left: 4px; }
  .legend-item.dimmed { opacity: 0.35; }
  .legend-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  .legend-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .legend-count { color: #666; font-size: 11px; }
  #stats { padding: 10px 14px; border-top: 1px solid #2a2a4e; font-size: 11px; color: #555; }
  #connectivity-status { padding: 8px 14px; border-top: 1px solid #2a2a4e; font-size: 12px; color: #4ECDC4; background: rgba(78, 205, 196, 0.1); }
</style>
</head>
<body>
<div id="graph"></div>
<div id="sidebar">
  <div id="search-wrap">
    <input id="search" type="text" placeholder="Search nodes..." autocomplete="off">
    <div id="search-results"></div>
  </div>
  <div id="info-panel">
    <h3>Node Info</h3>
    <div id="info-content"><span class="empty">Click a node to inspect it</span></div>
  </div>
  <div id="legend-wrap">
    <h3>Communities</h3>
    <div id="legend"></div>
  </div>
  <div id="connectivity-status">Graph Fully Connected</div>
  <div id="stats">''' + f'{len(data["nodes"])} nodes &middot; {len(data["links"])} edges &middot; {len(set(n["community"] for n in data["nodes"]))} communities' + '''</div>
</div>

<script>
// Graph data
const graphData = ''' + json.dumps(data) + ''';

const nodes = new vis.DataSet(graphData.nodes.map(n => ({
  id: n.id,
  label: n.label,
  color: { background: getCommunityColor(n.community), border: getCommunityColor(n.community), highlight: { background: '#ffffff', border: getCommunityColor(n.community) } },
  size: 5 + Math.min((graphData.links.filter(l => l._src === n.id || l._tgt === n.id).length * 0.15), 18),
  font: { size: 0, color: '#ffffff' },
  title: n.label,
  community: n.community,
  community_name: getCommunityName(n.community),
  source_file: n.source_file || '',
  file_type: n.file_type || 'code',
  degree: graphData.links.filter(l => l._src === n.id || l._tgt === n.id).length
})));

const edges = new vis.DataSet(graphData.links.map(l => ({
  from: l._src,
  to: l._tgt,
  weight: l.weight || 1.0,
  title: l.relation || 'connected',
  color: { color: getEdgeColor(l.relation), opacity: 0.7 }
})));

const container = document.getElementById('graph');
const data = { nodes: nodes, edges: edges };
const options = {
  physics: {
    enabled: true,
    barnesHut: {
      gravitationalConstant: -3000,
      centralGravity: 0.3,
      springLength: 120,
      springConstant: 0.04,
      damping: 0.09,
      avoidOverlap: 0
    },
    stabilization: {
      enabled: true,
      iterations: 1000,
      updateInterval: 25
    }
  },
  interaction: {
    hover: true,
    tooltipDelay: 100,
    hideEdgesOnDrag: true,
    navigationButtons: false,
    keyboard: false,
  },
  nodes: { shape: 'dot', borderWidth: 1.5 },
  edges: { smooth: { type: 'continuous', roundness: 0.2 }, selectionWidth: 3 },
};

const network = new vis.Network(container, data, options);

network.once('stabilizationIterationsDone', () => {
  network.setOptions({ physics: { enabled: false } });
});

function getCommunityColor(community) {
  const colors = {
    0: '#4E79A7',   // Core code
    1: '#F28E2C',   // Config
    2: '#E15759',   // Data
    3: '#76B7B2',   // Tools
    4: '#59A14F',   // Learning
    5: '#EDC949',   // Memory
    6: '#AF7AA1',   // Plugins
    7: '#FF9DA7',   // Tests
    8: '#9C755F',   // Docs
    9: '#BAB0AB',   // Utils
    100: '#FF6B6B', // Customers
    101: '#4ECDC4', // Services
    102: '#45B7D1', // Contacts
    200: '#96CEB4', // Sessions
    201: '#FECA57', // Summaries
    202: '#FF9FF3', // Messages
    203: '#54A0FF', // Tasks
    204: '#5F27CD', // Models
    205: '#00D2D3', // Providers
    300: '#FF9F43', // Calendar
    301: '#EE5A24'  // Event descriptions
  };
  return colors[community] || '#4E79A7';
}

function getEdgeColor(relation) {
  if (!relation) return '#666';
  if (relation.includes('database') || relation.includes('bridge')) return '#FF6B6B';
  if (relation.includes('session') || relation.includes('memory')) return '#96CEB4';
  if (relation.includes('has_service') || relation.includes('contact')) return '#4ECDC4';
  if (relation.includes('final_bridge') || relation.includes('isolated')) return '#FF9F43';
  return '#666';
}

function getCommunityName(community) {
  const names = {
    0: 'Core Code',
    1: 'Configuration',
    2: 'Data Files',
    3: 'Tools',
    4: 'Learning',
    5: 'Memory',
    6: 'Plugins',
    7: 'Tests',
    8: 'Documentation',
    9: 'Utilities',
    100: 'Customers',
    101: 'Services',
    102: 'Contacts',
    200: 'Sessions',
    201: 'Summaries',
    202: 'Messages',
    203: 'Tasks',
    204: 'Models',
    205: 'Providers',
    300: 'Calendar',
    301: 'Event Descriptions'
  };
  return names[community] || `Community ${community}`;
}

function showInfo(nodeId) {
  const n = nodes.get(nodeId);
  if (!n) return;
  const neighborIds = network.getConnectedNodes(nodeId);
  const neighborItems = neighborIds.slice(0, 10).map(nid => {
    const nb = nodes.get(nid);
    const color = nb ? getCommunityColor(nb.community) : '#555';
    return `<span class="neighbor-link" style="border-left-color:${color}" onclick="focusNode(${JSON.stringify(nid)})">${nb ? nb.label : nid}</span>`;
  }).join('');
  document.getElementById('info-content').innerHTML = `
    <div class="field"><b>${n.label}</b></div>
    <div class="field">Type: ${n.file_type || 'unknown'}</div>
    <div class="field">Community: ${n.community_name}</div>
    <div class="field">Source: ${n.source_file || '-'}</div>
    <div class="field">Connections: ${n.degree}</div>
    ${neighborIds.length ? `<div class="field" style="margin-top:8px;color:#aaa;font-size:11px">Neighbors (${neighborIds.length})</div><div id="neighbors-list">${neighborItems}</div>` : ''}
  `;
}

function focusNode(nodeId) {
  network.focus(nodeId, { scale: 1.4, animation: true });
  network.selectNodes([nodeId]);
  showInfo(nodeId);
}

let hoveredNodeId = null;
network.on('hoverNode', params => {
  hoveredNodeId = params.node;
  container.style.cursor = 'pointer';
});
network.on('blurNode', () => {
  hoveredNodeId = null;
  container.style.cursor = 'default';
});
container.addEventListener('click', () => {
  if (hoveredNodeId !== null) {
    showInfo(hoveredNodeId);
    network.selectNodes([hoveredNodeId]);
  } else {
    document.getElementById('info-content').innerHTML = '<span class="empty">Click a node to inspect it</span>';
  }
});
network.on('click', params => {
  if (params.nodes.length > 0) {
    showInfo(params.nodes[0]);
  } else if (hoveredNodeId === null) {
    document.getElementById('info-content').innerHTML = '<span class="empty">Click a node to inspect it</span>';
  }
});

const searchInput = document.getElementById('search');
const searchResults = document.getElementById('search-results');
searchInput.addEventListener('input', () => {
  const q = searchInput.value.toLowerCase().trim();
  searchResults.innerHTML = '';
  if (!q) { searchResults.style.display = 'none'; return; }
  const matches = nodes.get().filter(n => n.label.toLowerCase().includes(q)).slice(0, 20);
  if (!matches.length) { searchResults.style.display = 'none'; return; }
  searchResults.style.display = 'block';
  matches.forEach(n => {
    const el = document.createElement('div');
    el.className = 'search-item';
    el.textContent = n.label;
    el.style.borderLeft = `3px solid ${getCommunityColor(n.community)}`;
    el.style.paddingLeft = '8px';
    el.onclick = () => {
      network.focus(n.id, { scale: 1.5, animation: true });
      network.selectNodes([n.id]);
      showInfo(n.id);
      searchResults.style.display = 'none';
      searchInput.value = '';
    };
    searchResults.appendChild(el);
  });
});
document.addEventListener('click', e => {
  if (!searchResults.contains(e.target) && e.target !== searchInput)
    searchResults.style.display = 'none';
});

// Create legend
const communities = {};
nodes.get().forEach(n => {
  if (!communities[n.community]) {
    communities[n.community] = { count: 0, color: getCommunityColor(n.community), name: getCommunityName(n.community) };
  }
  communities[n.community].count++;
});

const legendEl = document.getElementById('legend');
Object.entries(communities).sort((a, b) => a[0] - b[0]).forEach(([comm_id, info]) => {
  const item = document.createElement('div');
  item.className = 'legend-item';
  item.innerHTML = `<div class="legend-dot" style="background:${info.color}"></div>
    <span class="legend-label">${info.name}</span>
    <span class="legend-count">${info.count}</span>`;
  item.onclick = () => {
    const isDimmed = item.classList.contains('dimmed');
    if (isDimmed) {
      item.classList.remove('dimmed');
    } else {
      item.classList.add('dimmed');
    }
    const updates = nodes.get().filter(n => n.community == comm_id).map(n => ({ id: n.id, hidden: !isDimmed }));
    nodes.update(updates);
  };
  legendEl.appendChild(item);
});
</script>
</body>
</html>'''

# Write the final HTML file
with open('graphify-out/graph_final_visualization.html', 'w') as f:
    f.write(html_template)

print("Created final comprehensive HTML visualization: graphify-out/graph_final_visualization.html")