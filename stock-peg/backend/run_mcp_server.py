#!/usr/bin/env python3
"""Start the Stock PEG MCP Server"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from mcp_server.server import run_server

if __name__ == "__main__":
    run_server()
