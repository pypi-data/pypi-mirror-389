import sys, os
import inspect
from .monitor import start_monitor_bg, LiveStack
import threading

# -----------------------------
# Monkey-patch built-in print
# -----------------------------
_print_lock = threading.Lock()
_original_print = print  # save original print

def _safe_print(*args, **kwargs):
    with _print_lock:
        _original_print(*args, **kwargs)

# Replace built-in print globally
print = _safe_print

AUTO = os.environ.get("LIVESTACK_AUTO_START", "1") == "1"

if AUTO and sys.modules.get("__main__") is not None:
    start_monitor_bg()
    
def __version__():
    """Return the version of the package."""
    return "0.4.0"