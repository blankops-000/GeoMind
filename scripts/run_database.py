#!/usr/bin/env python3
"""Convenience entry point for running the GeoMind database setup engine."""
import subprocess
import sys
import os

if __name__ == "__main__":
    setup_script = os.path.join(os.path.dirname(__file__), "setup_database.py")
    sys.exit(subprocess.call([sys.executable, setup_script] + sys.argv[1:]))
