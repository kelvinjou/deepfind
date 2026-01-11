from smolagents import CodeAgent, ToolCallingAgent
from smolagents.tools import Tool
from mcp import ClientSession
from mcp.client.sse import sse_client
import asyncio
import requests

# Option 1: Use Ollama for local model (recommended)
# First: brew install ollama && ollama pull gemma2:9b
from smolagents import LiteLLMModel
model = LiteLLMModel(model_id="ollama/gemma2:9b")

# Option 2: Use HuggingFace transformers directly (more VRAM needed)
# from smolagents import TransformersModel
# model = TransformersModel(model_id="google/gemma-2-9b-it", device_map="auto")


async def get_mcp_tools():
    """Connect to your FastAPI MCP server and get tools."""
    async with sse_client("http://127.0.0.1:7777/mcp/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            return tools


def create_agent_with_mcp():
    """Create a smolagent that uses your MCP server tools."""
    # For simpler setup, you can also define tools manually that call your API
    from smolagents import tool
    
    @tool
    def search_files(query: str) -> str:
        """Search through indexed files using semantic search.
        
        Args:
            query: The search query to find relevant files.
        """
        response = requests.get(
            "http://127.0.0.1:7777/query",
            params={"query_text": query}
        )
        return response.json()
    
    @tool
    def index_folder(folder_path: str) -> str:
        """Index a folder to generate embeddings for all files.
        
        Args:
            folder_path: The absolute path to the folder to index.
        """
        
        response = requests.post(
            "http://127.0.0.1:7777/dir/",
            json={"folderPath": folder_path}
        )
        return response.json()
    
    agent = ToolCallingAgent(
        tools=[search_files, index_folder],
        model=model,
    )
    return agent


if __name__ == "__main__":
    agent = create_agent_with_mcp()
    
    # Example usage
    result = agent.run("Search for files about machine learning")
    print(result)
