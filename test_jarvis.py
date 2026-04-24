# Test JARVIS Business Tools
import requests
import json

def test_jarvis():
    base_url = "http://127.0.0.1:8001"
    
    # Test health
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        print(f"[OK] Health Check: {r.status_code}")
        print(f"   Response: {r.json()}")
    except Exception as e:
        print(f"[FAIL] Health Check Failed: {e}")
        return
    
    # Test chat
    try:
        r = requests.post(
            f"{base_url}/api/chat",
            json={"prompt": "Hello, what can you do?"},
            timeout=30
        )
        print(f"\n[OK] Chat Test: {r.status_code}")
        resp = r.json()
        if 'response' in resp:
            print(f"   Response: {resp['response'][:100]}...")
        else:
            print(f"   Response: {json.dumps(resp, indent=2)[:100]}...")
    except Exception as e:
        print(f"[FAIL] Chat Test Failed: {e}")
    
    # Test tools list
    try:
        r = requests.get(f"{base_url}/api/tool-hub", timeout=10)
        print(f"\n[OK] Tools Hub: {r.status_code}")
        tools = r.json()
        business_tools = [t for t in tools.get('tools', []) if 'business' in t.get('name', '')]
        print(f"   Total Tools: {len(tools.get('tools', []))}")
        print(f"   Business Tools: {len(business_tools)}")
        if business_tools:
            print(f"   Sample: {[t['name'] for t in business_tools[:3]]}")
    except Exception as e:
        print(f"[FAIL] Tools Hub Failed: {e}")

if __name__ == "__main__":
    test_jarvis()
