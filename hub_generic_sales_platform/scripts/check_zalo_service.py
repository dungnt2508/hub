import sys
import os
sys.path.append(os.getcwd())

try:
    from app.infrastructure.external.zalo_service import ZaloService
    print("ZaloService imported successfully.")
    
    service = ZaloService()
    print("ZaloService instantiated.")
    
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
