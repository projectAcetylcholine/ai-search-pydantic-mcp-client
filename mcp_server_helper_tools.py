import os
import sys
from argparse import ArgumentParser
from typing import Literal
from pathlib import Path
import httpx
from dotenv import load_dotenv
from mcp.server import FastMCP

# Run this MCP server in SSE mode as:
# uv run mcp_server_helper_tools.py --transport sse

def setup_mcp_service(host_name: str, port: int):

    settings = {"host": host_name, "port": port}

    mcp = FastMCP("AI Search MCP Service", log_level="DEBUG", **settings)

    @mcp.tool(description="Reads the content of a local file and returns it as a string")
    def read_file_content(file_path: str, encoding: str = "utf-8") -> str:
        """
        Reads the content of a local file and returns it as a string.

        Args:
            file_path (str): The path to the local file.
            encoding (str): The character encoding to use (default is 'utf-8').

        Returns:
            str: The contents of the file as a string.

        Raises:
            FileNotFoundError: If the file does not exist.
            IOError: If the file cannot be read.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"No such file: '{file_path}'")

        return path.read_text(encoding=encoding)

    @mcp.tool(description="Fetches the contents of the given HTTP URL")
    async def fetch_url_content_async(url: str) -> str:
        """
        Fetches the contents of the given HTTP URL

        Args:
            url (str): The URL to fetch content from.

        Returns:
            str: The content retrieved from the URL.

        Raises:
            httpx.RequestError: If the request fails due to a network problem.
            httpx.HTTPStatusError: If the response status code is not 2xx.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    return mcp

def run_mcp_service():

    parser = ArgumentParser(description="Start the MCP service with provided or default configuration.")

    parser.add_argument('--transport', required=True, default='sse', help='Transport protocol (sse | stdio) (default: stdio)')
    parser.add_argument('--envFile', required=False, default='.env', help='Path to .env file (default: .env)')
    parser.add_argument('--host', required=False, default='0.0.0.0', help='Host IP or name for SSE (default: 0.0.0.0)')
    parser.add_argument('--port', required=False, type=int, default=3456, help='Port number for SSE (default: 8000)')

    # Parse the application arguments
    args = parser.parse_args()

    # Retrieve the specified transport
    transport: Literal["stdio", "sse"] = args.transport
    mcp_env_file = args.envFile

    # Set up the Host name and port
    mcp_host: str = args.host
    mcp_port: int = args.port

    if transport in ["sse", "stdio"]:
        print("")
        print("")
        print(f"Transport is specified as {transport}")
    else:
        print("")
        print("")
        print(f"Invalid transport was specified: transport={transport}")
        parser.print_help()
        sys.exit(1)

    # Check if envFile exists and load it
    if mcp_env_file and os.path.exists(mcp_env_file):
        load_dotenv(dotenv_path=mcp_env_file)
        print(f"Environment variables loaded from {mcp_env_file}")
    else:
        print(f"Env file '{mcp_env_file}' not found. Skipping environment loading.")

    mcp_service = setup_mcp_service(mcp_host, mcp_port)

    # Check all params and then run or print the help message
    mcp_service.run(transport)

if __name__ == "__main__":
    run_mcp_service()
