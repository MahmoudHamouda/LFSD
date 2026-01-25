import py_compile
import sys

try:
    py_compile.compile("routes/api_routes_chat.py", doraise=True)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
