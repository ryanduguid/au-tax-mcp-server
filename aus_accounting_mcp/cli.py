"""
CLI entrypoint for aus-accounting-mcp.
"""

import sys
from aus_accounting_mcp.server import run_stdio

def main():
    run_stdio()

if __name__ == "__main__":
    main()