"""
Entry point for running DeltaTask as a module.
This allows the package to be executed with 'python -m deltatask'.
"""

import sys
import os
import importlib.util

def main():
    """Main entry point for the DeltaTask MCP server."""
    # Get the path to server.py in the parent directory
    server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'server.py')

    # Load the server module dynamically
    spec = importlib.util.spec_from_file_location("server", server_path)
    server_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server_module)

    # Call the main function from server.py
    server_module.main()

if __name__ == "__main__":
    main()