#!/usr/bin/env python3
"""
JARVIS Black Box System - Simple Test
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_black_box():
    print("🧠 Testing JARVIS Black Box System")

    try:
        from Core.black_box import get_black_box, AgentType
        print("✅ Import successful")

        bb = get_black_box()
        print("✅ Black box initialized")

        # Test basic logging
        activity_id = bb.log_activity(
            agent_type=AgentType.JARVIS_CORE,
            agent_id="test_agent",
            activity_type=bb.ActivityType.TASK_START,
            content="Test task",
            metadata={"test": True}
        )
        print(f"✅ Logged activity: {activity_id}")

        # Test agent integration
        from Core.agent_integration import ClaudeCodeIntegrator
        integrator = ClaudeCodeIntegrator("test_123")
        session_id = integrator.start_session()
        print(f"✅ Started session: {session_id}")

        integrator.log_task_start("Test task")
        print("✅ Logged task start")

        summary = integrator.end_session("Test completed")
        print("✅ Ended session with summary")

        print("🎉 Black Box system test completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_black_box()