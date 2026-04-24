import json
import sqlite3
from datetime import datetime

# Load the connected graph
with open('graphify-out/graph_connected.json', 'r') as f:
    graph_data = json.load(f)

existing_nodes = {node['id']: node for node in graph_data['nodes']}
existing_links = {(link['_src'], link['_tgt']): link for link in graph_data['links']}

def add_node(node_id, label, community, source_file, file_type='database'):
    if node_id not in existing_nodes:
        existing_nodes[node_id] = {
            'id': node_id,
            'label': label,
            'community': community,
            'source_file': source_file,
            'file_type': file_type
        }
        graph_data['nodes'].append(existing_nodes[node_id])

def add_link(src, tgt, relation='related_to', weight=1.0):
    link_key = (src, tgt)
    if link_key not in existing_links:
        link = {
            '_src': src,
            '_tgt': tgt,
            'relation': relation,
            'weight': weight
        }
        existing_links[link_key] = link
        graph_data['links'].append(link)

# Extract relationships from customers database
print("Extracting customer relationships...")
try:
    conn = sqlite3.connect('data/customers/customers.db')
    cursor = conn.cursor()

    # Get customers and their services
    cursor.execute('''
        SELECT c.id, c.name, c.phone, c.email, s.service_type, s.details, s.status
        FROM customers c
        LEFT JOIN services s ON c.id = s.customer_id
    ''')
    customer_data = cursor.fetchall()

    for row in customer_data:
        customer_id, name, phone, email, service_type, details, status = row
        customer_node_id = f"customer_{customer_id}"

        add_node(customer_node_id, f"Customer: {name}", 100, 'data/customers/customers.db', 'customer')

        if service_type:
            service_node_id = f"service_{customer_id}_{service_type.replace(' ', '_')}"
            add_node(service_node_id, f"Service: {service_type} ({status})", 101, 'data/customers/customers.db', 'service')

            add_link(customer_node_id, service_node_id, 'has_service', 0.9)

        if phone:
            phone_node_id = f"phone_{phone}"
            add_node(phone_node_id, f"Phone: {phone}", 102, 'data/customers/customers.db', 'contact')
            add_link(customer_node_id, phone_node_id, 'contact_info', 0.8)

        if email:
            email_node_id = f"email_{email}"
            add_node(email_node_id, f"Email: {email}", 102, 'data/customers/customers.db', 'contact')
            add_link(customer_node_id, email_node_id, 'contact_info', 0.8)

    conn.close()
except Exception as e:
    print(f"Error processing customers database: {e}")

# Extract relationships from memory database
print("Extracting memory relationships...")
try:
    conn = sqlite3.connect('memory/memory.db')
    cursor = conn.cursor()

    # Get sessions and their messages/tasks
    cursor.execute('''
        SELECT s.session_id, s.channel, s.summary, m.role, m.text, t.task_class, t.model, t.provider, t.success
        FROM sessions s
        LEFT JOIN messages m ON s.session_id = m.session_id
        LEFT JOIN task_runs t ON s.session_id = t.session_id
        LIMIT 500
    ''')
    memory_data = cursor.fetchall()

    for row in memory_data:
        session_id, channel, summary, role, text, task_class, model, provider, success = row
        session_node_id = f"session_{session_id}"

        add_node(session_node_id, f"Session: {channel} ({session_id[:8]})", 200, 'memory/memory.db', 'session')

        if summary:
            summary_node_id = f"summary_{session_id}"
            add_node(summary_node_id, f"Summary: {summary[:50]}...", 201, 'memory/memory.db', 'summary')
            add_link(session_node_id, summary_node_id, 'has_summary', 0.9)

        if role and text:
            message_node_id = f"message_{session_id}_{role}"
            add_node(message_node_id, f"Message: {role} - {text[:30]}...", 202, 'memory/memory.db', 'message')
            add_link(session_node_id, message_node_id, 'contains_message', 0.8)

        if task_class:
            task_node_id = f"task_{session_id}_{task_class}"
            success_status = "success" if success else "failed"
            add_node(task_node_id, f"Task: {task_class} ({success_status})", 203, 'memory/memory.db', 'task')
            add_link(session_node_id, task_node_id, 'executed_task', 0.85)

            if model:
                model_node_id = f"model_{model}"
                add_node(model_node_id, f"Model: {model}", 204, 'memory/memory.db', 'model')
                add_link(task_node_id, model_node_id, 'used_model', 0.7)

            if provider:
                provider_node_id = f"provider_{provider}"
                add_node(provider_node_id, f"Provider: {provider}", 205, 'memory/memory.db', 'provider')
                add_link(task_node_id, provider_node_id, 'used_provider', 0.7)

    conn.close()
except Exception as e:
    print(f"Error processing memory database: {e}")

# Extract relationships from calendar database (if any)
print("Extracting calendar relationships...")
try:
    conn = sqlite3.connect('jarvis_calendar.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, title, event_time, description FROM events')
    events = cursor.fetchall()

    for event_id, title, event_time, description in events:
        event_node_id = f"event_{event_id}"
        add_node(event_node_id, f"Event: {title}", 300, 'jarvis_calendar.db', 'calendar_event')

        if description:
            desc_node_id = f"event_desc_{event_id}"
            add_node(desc_node_id, f"Description: {description[:50]}...", 301, 'jarvis_calendar.db', 'event_description')
            add_link(event_node_id, desc_node_id, 'has_description', 0.8)

    conn.close()
except Exception as e:
    print(f"Error processing calendar database: {e}")

# Save the updated graph
with open('graphify-out/graph_connected_with_db.json', 'w') as f:
    json.dump(graph_data, f, indent=2)

print(f"Added database relationships. Total nodes: {len(graph_data['nodes'])}, Total links: {len(graph_data['links'])}")
print("Saved to: graphify-out/graph_connected_with_db.json")