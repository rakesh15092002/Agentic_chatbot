import os
import shutil
import logging
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class GitHubMCPClient:
    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None

    async def connect(self):
        """Connect to GitHub MCP Server"""
        token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        npx_path = shutil.which("npx")

        if not token:
            raise ValueError("GITHUB_PERSONAL_ACCESS_TOKEN environment variable is not set")
        
        if not npx_path:
            raise ValueError("Node.js (npx) not found. Please install Node.js")

        logger.info(f"🔌 Starting GitHub MCP Server with npx at: {npx_path}")

        # Start the Official GitHub MCP Server
        server_params = StdioServerParameters(
            command=npx_path,
            args=["-y", "@modelcontextprotocol/server-github"],
            env={**os.environ, "GITHUB_PERSONAL_ACCESS_TOKEN": token}
        )

        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )
            
            await self.session.initialize()
            logger.info("✅ Connected to GitHub MCP Server successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to GitHub MCP: {e}", exc_info=True)
            raise

    async def list_tools(self):
        """List all available GitHub tools"""
        if not self.session:
            await self.connect()
        
        try:
            result = await self.session.list_tools()
            logger.info(f"📋 Available tools from MCP: {[tool.name for tool in result.tools]}")
            
            # Convert to OpenAI/Groq compatible format
            tools = []
            for tool in result.tools:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or f"GitHub tool: {tool.name}",
                        "parameters": tool.inputSchema or {"type": "object", "properties": {}}
                    }
                })
            
            return tools
            
        except Exception as e:
            logger.error(f"❌ Error listing tools: {e}", exc_info=True)
            raise

    async def call_tool(self, name: str, args: dict):
        """Call a specific GitHub tool"""
        if not self.session:
            await self.connect()
        
        try:
            logger.info(f"🔧 Calling MCP tool '{name}' with args: {args}")
            result = await self.session.call_tool(name, args)
            
            # Extract text content from result
            if hasattr(result, 'content'):
                text_parts = []
                for content_item in result.content:
                    if hasattr(content_item, 'type') and content_item.type == "text":
                        text_parts.append(content_item.text)
                
                response = "\n".join(text_parts) if text_parts else str(result)
                logger.info(f"✅ Tool '{name}' returned {len(response)} characters")
                return response
            else:
                logger.warning(f"⚠️ Unexpected result format from tool '{name}': {type(result)}")
                return str(result)
                
        except Exception as e:
            error_msg = f"Error calling tool '{name}': {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            raise Exception(error_msg)

    async def close(self):
        """Close the MCP connection"""
        try:
            if self.exit_stack:
                await self.exit_stack.aclose()
                logger.info("🔌 GitHub MCP connection closed")
        except Exception as e:
            logger.error(f"Error closing MCP client: {e}", exc_info=True)