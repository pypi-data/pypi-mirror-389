import sys
import threading
import inspect
import time
from threading import Thread
import os
import builtins
import threading
import inspect
import atexit
import importlib.util
import sysconfig

# Global lock for thread-safe printing
_print_lock = threading.Lock()

def safe_print(s, end='\r', max_len=0):
    """Thread-safe printing for inline updates"""
    with _print_lock:
        print(s.ljust(max_len), end=end, flush=True)

#### SINGLETON LOGIC
_monitor_instance = None
class LiveStack:
    def __init__(self, interval=1, max_depth=5, min_display_time=1, delimiter = " >", time_format="short", hide_unnecessary_current_time = True, decimals=1,display_current_time=False, display_total_time=False,
                 total_threshold = None,current_threshold= None, avoid_crash=True, max_func_name_length = 15):
        """
        interval: how often to update the display (seconds)
        max_depth: max number of functions to show
        min_display_time: minimum time a stack must stay before updating (reduces flicker)
        """
        self.interval = interval
        self.max_depth = max_depth
        self.min_display_time = min_display_time
        self._running = False
        self._last_stack_str = ""
        self._max_len = 0
        self.project_root = os.getcwd()  # optional: filter by project files
        self.delimiter = delimiter
        self.last_print_time = time.time()
        self.last_change_stack_time = time.time()
        self.last_stack = []
        self.decimals = decimals
        self.time_format = time_format
        self.display_current_time = display_current_time
        self.display_total_time = display_total_time
        self.hide_unnecessary_current_time = hide_unnecessary_current_time
        self.total_threshold = total_threshold
        self.current_threshold = current_threshold
        self._time_info = {}  # {func_name: {"cumulative": float, "active_since": float or None}}
        self.max_func_name_length = max_func_name_length
        self.avoid_crash = avoid_crash
        
    def _get_main_stack(self):

        main_thread = threading.main_thread()
        frame = sys._current_frames().get(main_thread.ident)
        raw_stack = []

        stdlib_path = sysconfig.get_path("stdlib")

        # Step 1: collect all frames with library info
        while frame and len(raw_stack) < self.max_depth:
            name = frame.f_code.co_name
            filename = frame.f_code.co_filename

            # Replace <module> with main
            if name == "<module>":
                name = "main"
            # shorten
            if self.max_func_name_length:
                name = self.shorten_name(name)
            # Skip stdlib (but keep site-packages)
            if filename.startswith(stdlib_path) and "site-packages" not in filename:
                frame = frame.f_back
                continue

            # Detect library
            try:
                mod = inspect.getmodule(frame)
                if mod and hasattr(mod, "__name__"):
                    lib = mod.__name__.split(".")[0]
                else:
                    lib = "builtin"
            except Exception:
                lib = "?"

            raw_stack.append((name, filename, lib))
            frame = frame.f_back

        # Step 2: reverse to display order
        stack = list(reversed(raw_stack))

        # Step 3: hide repeated libraries in forward order
        display_stack = []
        last_lib = None
        for name, filename, lib in stack:
            if lib == "__main__" or filename.startswith(self.project_root):
                display_name = f" {name}"
                last_lib = None  # reset on user code
            else:
                if lib == last_lib:
                    display_name = f"· {name}"  # continuation of same library
                else:
                    display_name = f"[{lib}] {name}"
                    last_lib = lib
            display_stack.append(display_name)

        return display_stack

    
    def _format_time(self, seconds):
        if callable(self.time_format):
            return self.time_format(seconds)

        if self.time_format == "short":  # default
            if seconds >= 60*60*3:
                return f"{(seconds//3600):.0f}h"
            elif seconds >= 60*3:
                return f"{(seconds//60):.0f}m"
            else:
                return f"{seconds:.{self.decimals}f}s"
        elif self.time_format == "seconds": 
            return f"{seconds:.{self.decimals}f}s"
        elif self.time_format == "ms":
            return f"{seconds*1000:.{self.decimals}f}ms"
        elif self.time_format == "hh:mm:ss":
            h, rem = divmod(seconds, 3600)
            m, s = divmod(rem, 60)
            return f"{int(h):02}:{int(m):02}:{s:0{2+self.decimals+int(self.decimals>0)}.{self.decimals}f}"
        else:
            return f"{seconds:.{self.decimals}f}s"
    
    def _time_decorator(self,part):
        if part == "":
            return ""
        return f" {part}"
        return f"({part})"
    
    def _format_stack(self, stack):
        """Return formatted stack string with per-function times."""
        parts = []
        now = time.time()
        for func in stack:
            info = self._time_info.get(func, {"cumulative": 0.0, "active_since": None})
            current = 0.0
            if info["active_since"] is not None:
                current = now - info["active_since"]
            total = info["cumulative"]
            cur_str = self._format_time(current)
            tot_str = self._format_time(total)
            display_current_time = self.display_current_time
            display_total_time = self.display_total_time
            
            if self.current_threshold and current < self.current_threshold:
                display_current_time = False
            if self.total_threshold and total < self.total_threshold:
                display_total_time = False
            
            # add time threshold
            if abs(current - total) < 0.1 and self.hide_unnecessary_current_time and display_total_time: #hide current time if unnecessary and we have total time
                display_current_time = False
                
            if display_current_time and display_total_time: #displaying or not only depends on the local variables.
                part = f"{cur_str}/{tot_str}"
            elif display_total_time:
                part = tot_str
            elif display_current_time:
                part = cur_str
            else:
                part = ""
                
            func_str = func  #add code that knows of library
            part = func_str + self._time_decorator(part)
            parts.append(part)
            
        return self.delimiter.join(parts)
    
    def _print_stack(self, stack_list):
        now = time.time()
        stack_str = self._format_stack(stack_list)
        # Only update if changed and held longer than min_display_time
        if stack_str != self._last_stack_str:
            safe_print(stack_str, end='\r', max_len=self._max_len)
            self._max_len = max(self._max_len, len(stack_str))
            self.last_print_time = now
            self._last_stack_str = stack_str
    
    def shorten_name(self,name, max_len=15):
        if len(name) <= max_len:
            return name
        half = (max_len - 1) // 2
        return name[:half] + "…" + name[-half:]

    def _run(self):
        while self._running:
            if self.avoid_crash:
                try:
                    stack = self._get_main_stack()
                    self._update_timing(stack)
                    now = time.time()
                    if now < self.last_change_stack_time + self.min_display_time:
                        stack = self.last_stack
                    else:
                        self.last_change_stack_time = time.time()
                        self.last_stack = stack
                    self._print_stack(stack)
                except:
                    try:
                        self._print_stack(["LiveStack - Unknown error"])
                    except:
                        pass
            else:
                stack = self._get_main_stack()
                self._update_timing(stack)
                now = time.time()
                if now < self.last_change_stack_time + self.min_display_time:
                    stack = self.last_stack
                else:
                    self.last_change_stack_time = time.time()
                    self.last_stack = stack
                self._print_stack(stack)
            time.sleep(self.interval)

    def start(self):
        if not self._running:
            self._running = True
            thread = Thread(target=self._run, daemon=True)
            thread.start()
            atexit.register(self._cleanup)
    
    # Optional: expose to user
    def configure(**kwargs):
        """Restart the LiveStack monitor with new settings."""
        return start_monitor_bg(**kwargs)
    
    def _update_timing(self, stack):
        """Update per-function timing info for all functions in the current stack."""
        now = time.time()

        # Mark active functions
        active_funcs = set(stack)
        for func in active_funcs:
            if func not in self._time_info:
                self._time_info[func] = {"cumulative": 0.0, "active_since": now, "last_update":now}
            elif self._time_info[func]["active_since"] is None:
                self._time_info[func]["active_since"] = now
                self._time_info[func]["last_update"] = now

        # Update cumulative times
        for func, info in self._time_info.items():
            if info["active_since"] is not None and info["last_update"] is not None:
                # Add elapsed since last update
                elapsed = now - info["last_update"]
                info["cumulative"] += elapsed
                info["last_update"] = now  # reset timestamp for next interval

        # Mark inactive functions as not active
        for func in set(self._time_info.keys()) - active_funcs:
            self._time_info[func]["active_since"] = None
            self._time_info[func]["last_update"] = None

    def stop(self):
        self._running = False
    
    def _cleanup(self):
        """Called on program exit"""
        self._running = False
        # Clear the last inline line
        with _print_lock:
            print(" " * self._max_len, end="\r", flush=True)
    def test(self):
        time.sleep(4)
    def test2(self):
        self.test()

# Convenience function
def start_monitor_bg(**kwargs):
    global _monitor_instance
    if _monitor_instance:
        _monitor_instance._cleanup()
        _monitor_instance = None
    _monitor_instance = LiveStack(**kwargs)
    _monitor_instance.start()
    return _monitor_instance

def stop_monitor():
    global _monitor_instance
    if _monitor_instance:
        _monitor_instance._cleanup()
        _monitor_instance = None

