import sys
import logging
import os
import anyio
import click
import re
import mcp.types as types
from .document_library_api import get_document_library_list
from .retrival_service_api import watsonx_data_query_handler
from fastmcp.server.server import FastMCP
from mcp.types import Tool as MCPTool


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

class mcp_server(FastMCP):
    async def _list_tools_mcp(self) -> list[MCPTool]:
        tool_definitions = []
        
        # Step 1: Retrieve document libraries
        document_library_definitions = get_document_library_list()
        logger.debug(f"Document library list: {document_library_definitions}")

        # Step 2: Prepare ASCII-safe validation pattern
        ascii_safe_pattern = re.compile(r'^[a-z0-9_-]+$', re.IGNORECASE)

        logger.info("Loading tools from document libraries...")
        for idx, tool_config in enumerate(document_library_definitions, start=1):
            if not isinstance(tool_config, dict):
                logger.warning(f"[{idx}] Skipping invalid entry (not a dictionary): {tool_config}")
                continue

            name_part = tool_config.get('document_library_name')
            id_part = tool_config.get('document_library_id')

            if not name_part or not id_part:
                logger.warning(f"[{idx}] Missing required fields in config: {tool_config}")
                continue

            tool_name = (str(name_part) + str(id_part)).replace("-", "_").replace(" ", "_")
            logger.debug(f"[{idx}] Generated tool_name: {tool_name}")

            # Step 3: Validate tool_name with ASCII-safe rule
            if not ascii_safe_pattern.match(tool_name):
                logger.warning(f"[{idx}] Skipping tool '{tool_name}' (contains non-ASCII or invalid characters)")
                continue

            try:
                tool_def = types.Tool(
                    name=tool_name,
                    description=tool_config.get('document_library_description', "No description provided"),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                        },
                        "required": ["query"]
                    }
                )
                tool_definitions.append(tool_def)
                logger.info(f"[{idx}] Added tool definition for: {tool_name}")
            except (ValueError, TypeError) as e:
                logger.warning(f"[{idx}] Skipping tool due to configuration error: {e}", exc_info=True)
            except Exception as e:
                logger.warning(f"[{idx}] Skipping tool due to unexpected error: {e}", exc_info=True)

        logger.info(f"=== Completed tool listing: {len(tool_definitions)} tools discovered ===")
        logger.debug(f"Tool definitions: {tool_definitions}")
        return tool_definitions
    
    async def _call_tool_mcp(
        self,
        name: str,
        arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        document_library_definitions = get_document_library_list()
        logger.info(f"Document library list : {document_library_definitions}")

        for tool_config in document_library_definitions:
            if not isinstance(tool_config, dict):
                logger.info(
                    f"Skipping invalid entry in document libraries (not a dictionary): {tool_config}")
                continue
            tool_name = (tool_config.get('document_library_name') + tool_config.get(
                'document_library_id')).replace("-", "_").replace(" ", "_")
            logger.info(f"Document library tool name : {tool_name}")
            if tool_name == name:
                query = arguments["query"]
                try:
                    result = watsonx_data_query_handler(query, tool_config.get(
                        'document_library_id'), tool_config.get('container_type'), tool_config.get('container_id'))
                    return [types.TextContent(type="text", text=result)]
                except Exception as e:
                    logger.error(
                        f"Error calling tool '{name}' with query '{query}': {e}", exc_info=True)
                    return [types.TextContent(type="text", text=f"Error executing tool '{name}': {str(e)}")]
        logger.error(f"Tool not found: {name}")
        return [types.TextContent(type="text", text=f"Tool not found: {name}, toolname {tool_name}")]

app = mcp_server("ibm-watsonxdata-dl-retrieval-mcp-server")
    
@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option("--transport",type=click.Choice(["stdio", "sse"]), default="sse", help="Transport type")
def run_mcp_server(port: int, transport: str):
    """Runs the MCP server."""

    if transport == "sse":
        logger.info(f"Starting MCP server with SSE transport on port {port}...")
        async def arun():
            await app.run_sse_async(host="127.0.0.1",
                    port=port,
                    log_level=(os.getenv("LOG_LEVEL", "").upper() == "DEBUG"),
                )
        try:
            anyio.run(arun)
        except KeyboardInterrupt:
            logger.info("\nServer stopped by user.")

    elif transport == "stdio":
        logger.info("Starting MCP server with stdio transport")
        async def arun():
            await app.run_async("stdio") 
        try:
            anyio.run(arun)
        except KeyboardInterrupt:
            logger.info("\nServer stopped by user.")
    else:
        logger.critical(f"Unknown transport: {transport}")
        sys.exit(1)
