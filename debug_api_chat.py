from fastapi.testclient import TestClient
from Core import main
from Core import runtime_orchestrator
from Core import tool_router
from Core.tool_contracts import ToolResult

# Apply test monkeypatches
main.run_chat_runtime = runtime_orchestrator.run_chat_runtime
main.get_provider_manager = lambda: object()

# Monkeypatch open_app tool
tool_router._run_open_app = lambda parameters: ToolResult(
    True,
    "Opened firefox.",
    details={
        "app_name": parameters.get("app_name", ""),
        "running": True,
        "process_count": 1,
        "window_title": "Firefox",
    },
)

with TestClient(main.app) as client:
    resp = client.post(
        "/api/chat",
        json={
            "prompt": "open firefox",
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "session_id": "bb-open-app",
        },
    )
    print('status_code=', resp.status_code)
    try:
        print('json=', resp.json())
    except Exception as e:
        print('json decode error', e)
    print('text=', resp.text)
