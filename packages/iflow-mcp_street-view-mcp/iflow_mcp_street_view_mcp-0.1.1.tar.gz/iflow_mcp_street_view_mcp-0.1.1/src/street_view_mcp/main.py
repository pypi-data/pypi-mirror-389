"""Entry point for the Street View MCP server."""

import sys
# Use absolute import instead of relative import
from street_view_mcp.server import mcp

def main():
    """Run the Street View MCP server."""
    try:
        # Start the MCP server using stdio transport
        mcp.run()
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    main()