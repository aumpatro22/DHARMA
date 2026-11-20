#!/usr/bin/env python3
"""
server.py — Root CLI entrypoint for Tactical Intelligence Web Interface & API
Delegates to dharma.api.server for clean domain architecture.
"""
import os
import sys
import time
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def ensure_port_free(port: int = 8008):
    """Automatically frees the port from any stale zombie/background processes."""
    try:
        res = subprocess.run(["fuser", f"{port}/tcp"], capture_output=True, text=True)
        pids = res.stdout.strip().split()
        curr_pid = str(os.getpid())
        for pid in pids:
            pid = pid.strip()
            if pid and pid != curr_pid:
                try:
                    os.kill(int(pid), 9)
                    time.sleep(0.3)
                except (ProcessLookupError, PermissionError):
                    pass
    except Exception:
        pass

from dharma.api.server import app

if __name__ == "__main__":
    ensure_port_free(8008)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
