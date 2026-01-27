#!/usr/bin/env python3
"""
XiCON CLI - Entry point script

Usage:
    python xicon_cli.py generate <workflow.json> [options]
    python xicon_cli.py add-node <node_type> <github_url>
    python xicon_cli.py add-model <filename> <url>
    python xicon_cli.py analyze <workflow.json>
    python xicon_cli.py list [nodes|models|all]

Examples:
    python xicon_cli.py generate XiCON/XiCON_Dance_SCAIL/XiCON_Dance_SCAIL(10s).json
    python xicon_cli.py analyze XiCON/XiCON_Dance_SCAIL/XiCON_Dance_SCAIL(10s).json
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.cli.commands import main

if __name__ == "__main__":
    main()
