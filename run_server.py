#!/usr/bin/env python3
"""Direct server start with error handling and configuration"""
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

