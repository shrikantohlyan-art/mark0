#!/usr/bin/env python3
"""Direct server start with error handling and configuration"""
import socket
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Loading configuration...")
    try:
        from config_manager import get_config
        config = get_config()
        host = config.get("backend.host", "0.0.0.0")
        port = config.get("backend.port", 8001)
    except ImportError as e:
        print(f"[WARN] config_manager missing: {e}")
        host = "0.0.0.0"
        port = 8001
    
    print("Attempting to import Core.main...")
    from Core.main import app
    print("OK: App imported successfully")

    def _is_port_available(hostname: str, port_number: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((hostname, port_number))
                return True
            except OSError:
                return False

    def _choose_available_port(hostname: str, start_port: int, max_tries: int = 10) -> int:
        if _is_port_available(hostname, start_port):
            return start_port
        fallback = start_port + 1
        for _ in range(max_tries - 1):
            if _is_port_available(hostname, fallback):
                print(f"WARNING: Port {start_port} unavailable. Falling back to {fallback}.")
                return fallback
            fallback += 1
        return start_port

    port = _choose_available_port(host, int(port))
    print(f"Starting uvicorn on {host}:{port}...")
    import uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
except Exception as e:
    print(f"ERROR: {type(e).__name__}")
    print(f"Message: {e}")
    import traceback
    traceback.print_exc()

