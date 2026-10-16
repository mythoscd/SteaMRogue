# %%
"""
SteaMRogue Root Entrypoint Wrapper
Delegates directly to backend/app.py for seamless local execution.
"""
import importlib.util
import os
import sys

_backend_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "app.py")
_backend_dir = os.path.dirname(_backend_app_path)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

spec = importlib.util.spec_from_file_location("backend_app", _backend_app_path)
backend_mod = importlib.util.module_from_spec(spec)
sys.modules["backend_app"] = backend_mod
spec.loader.exec_module(backend_mod)

for attr in dir(backend_mod):
    if not attr.startswith("__"):
        globals()[attr] = getattr(backend_mod, attr)

if __name__ == "__main__":
    backend_mod.main()
