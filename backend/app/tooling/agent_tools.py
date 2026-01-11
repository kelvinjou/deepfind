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
    from typing import List
    
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
    
    @tool
    def move_files(file_paths: List[str], target_directory: str) -> str:
        """Move files to a specified directory.
        
        Args:
            file_paths: List of absolute file paths to move.
            target_directory: The target directory path.
        """
        response = requests.post(
            "http://127.0.0.1:7777/files/move",
            json={"filePaths": file_paths, "targetDirectory": target_directory}
        )
        return response.json()
    
    @tool
    def convert_files(file_paths: List[str], target_extension: str) -> str:
        """Convert files to a different extension by copying with new extension.
        
        Args:
            file_paths: List of absolute file paths to convert.
            target_extension: The target file extension (e.g., 'txt', 'md').
        """
        response = requests.post(
            "http://127.0.0.1:7777/files/convert",
            json={"filePaths": file_paths, "targetExtension": target_extension}
        )
        return response.json()
    
    @tool
    def rename_files(file_paths: List[str], new_names: List[str]) -> str:
        """Rename files with new names.
        
        Args:
            file_paths: List of absolute file paths to rename.
            new_names: List of new file names (must match length of file_paths).
        """
        response = requests.post(
            "http://127.0.0.1:7777/files/rename",
            json={"filePaths": file_paths, "newNames": new_names}
        )
        return response.json()
    
    @tool
    def tag_files(file_paths: List[str], tag: str, color: int = 0) -> str:
        """Tag files with macOS Finder tags.
        
        Args:
            file_paths: List of absolute file paths to tag.
            tag: The tag name (e.g., 'Work', 'Important').
            color: Color index 0-7 (0=none, 1=gray, 2=green, 3=purple, 4=blue, 5=yellow, 6=red, 7=orange).
        """
        response = requests.post(
            "http://127.0.0.1:7777/files/tag",
            json={"filePaths": file_paths, "tag": tag, "color": color}
        )
        return response.json()
    
    @tool
    def get_files_with_tag(directory: str, tag: str) -> str:
        """Get all files in a directory that have a specific macOS Finder tag.
        
        Args:
            directory: The directory path to search in.
            tag: The tag name to search for.
        """
        response = requests.post(
            "http://127.0.0.1:7777/files/get-by-tag",
            json={"directory": directory, "tag": tag}
        )
        return response.json()
    
    @tool
    def search_files_by_pattern(directory: str, pattern: str) -> str:
        """Search for files matching a name pattern.
        
        Args:
            directory: The directory path to search in.
            pattern: The pattern to match in filenames.
        """
        response = requests.post(
            "http://127.0.0.1:7777/files/search-pattern",
            json={"directory": directory, "pattern": pattern}
        )
        return response.json()
    
    @tool
    def search_files_by_tags(directory: str, tag_key: str, tag_value: str) -> str:
        """Search for files by metadata tags in .meta files.
        
        Args:
            directory: The directory path to search in.
            tag_key: The metadata key to search for.
            tag_value: The metadata value to match.
        """
        response = requests.post(
            "http://127.0.0.1:7777/files/search-tags",
            json={"directory": directory, "tagKey": tag_key, "tagValue": tag_value}
        )
        return response.json()
    
    @tool
    def filter_files_by_date(directory: str, start_date: float, end_date: float) -> str:
        """Filter files by modification date range.
        
        Args:
            directory: The directory path to search in.
            start_date: Start of date range as Unix timestamp.
            end_date: End of date range as Unix timestamp.
        """
        response = requests.post(
            "http://127.0.0.1:7777/files/filter-by-date",
            json={"directory": directory, "startDate": start_date, "endDate": end_date}
        )
        return response.json()
    
    @tool
    def filter_files_by_size(directory: str, min_size: int, max_size: int) -> str:
        """Filter files by size range.
        
        Args:
            directory: The directory path to search in.
            min_size: Minimum file size in bytes.
            max_size: Maximum file size in bytes.
        """
        response = requests.post(
            "http://127.0.0.1:7777/files/filter-by-size",
            json={"directory": directory, "minSize": min_size, "maxSize": max_size}
        )
        return response.json()
    
    @tool
    def filter_files_by_type(directory: str, file_extension: str) -> str:
        """Filter files by file extension.
        
        Args:
            directory: The directory path to search in.
            file_extension: The file extension to filter by (e.g., '.txt', '.pdf').
        """
        response = requests.post(
            "http://127.0.0.1:7777/files/filter-by-type",
            json={"directory": directory, "fileExtension": file_extension}
        )
        return response.json()
    
    @tool
    def copy_files(file_paths: List[str], target_directory: str) -> str:
        """Copy files to a target directory.
        
        Args:
            file_paths: List of absolute file paths to copy.
            target_directory: The target directory path.
        """
        response = requests.post(
            "http://127.0.0.1:7777/files/copy",
            json={"filePaths": file_paths, "targetDirectory": target_directory}
        )
        return response.json()
    
    @tool
    def copy_directory(source_directory: str, target_directory: str) -> str:
        """Copy an entire directory to a new location.
        
        Args:
            source_directory: The source directory path to copy.
            target_directory: The target directory path.
        """
        response = requests.post(
            "http://127.0.0.1:7777/files/copy-directory",
            json={"sourceDirectory": source_directory, "targetDirectory": target_directory}
        )
        return response.json()
    
    @tool
    def get_recent_files(directory: str, count: int) -> str:
        """Get the most recently modified files in a directory.
        
        Args:
            directory: The directory path to search in.
            count: Number of recent files to return.
        """
        response = requests.post(
            "http://127.0.0.1:7777/files/recent",
            json={"directory": directory, "count": count}
        )
        return response.json()
    
    agent = ToolCallingAgent(
        tools=[
            search_files,
            index_folder,
            move_files,
            convert_files,
            rename_files,
            tag_files,
            get_files_with_tag,
            search_files_by_pattern,
            search_files_by_tags,
            filter_files_by_date,
            filter_files_by_size,
            filter_files_by_type,
            copy_files,
            copy_directory,
            get_recent_files,
        ],
        model=model,
    )
    return agent


if __name__ == "__main__":
    agent = create_agent_with_mcp()
    
    # Example usage
    result = agent.run("Search for files about machine learning")
    print(result)
