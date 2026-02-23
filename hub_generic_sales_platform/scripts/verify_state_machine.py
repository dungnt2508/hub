import sys
import os

# Create a minimal mock of the environment to avoid full app loading issues
sys.path.append(os.getcwd())

try:
    from app.core.domain.state_machine import StateMachine, LifecycleState

    allowed = StateMachine.get_allowed_tools("IDLE")
    print(f"Allowed tools for IDLE: {allowed}")

    if "get_offering_details" in allowed:
        print("SUCCESS: get_offering_details is enabled for IDLE.")
        sys.exit(0)
    else:
        print("FAILURE: get_offering_details is NOT enabled for IDLE.")
        sys.exit(1)
except ImportError as e:
    print(f"ImportError: {e}")
    # Fallback verification by reading file if import fails due to dependencies
    with open("app/core/domain/state_machine.py", "r", encoding="utf-8") as f:
        content = f.read()
        import re
        # Rough check regex for IDLE block
        match = re.search(r'LifecycleState\.IDLE:\s*\{([^}]+)\}', content, re.DOTALL)
        if match and "get_offering_details" in match.group(1):
             print("SUCCESS (Static Analysis): get_offering_details found in IDLE set.")
             sys.exit(0)
        else:
             print("FAILURE: Could not confirm via static analysis.")
             sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
