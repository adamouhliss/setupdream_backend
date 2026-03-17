import sys
import os
sys.path.append(os.getcwd())

try:
    from app.schemas import product
    print("Import success")
except Exception as e:
    import traceback
    traceback.print_exc()
