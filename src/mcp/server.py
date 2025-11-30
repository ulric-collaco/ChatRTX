from src.mcp.tools import ToolSet
import json

class MCPServer:
    def __init__(self, tool_set: ToolSet):
        self.tools = tool_set
        self.tool_definitions = [
            {
                "name": "search_notes",
                "description": "Search for information in the user's study notes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query."
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_notes",
                "description": "List all available study notes files.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

    def get_tool_definitions(self):
        return self.tool_definitions

    def call_tool(self, tool_name, arguments):
        """
        Execute a tool call.
        arguments can be a dict or a JSON string.
        """
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except:
                pass # might be a raw string if simple
        
        if tool_name == "search_notes":
            return self.tools.search_notes(arguments.get("query"))
        elif tool_name == "list_notes":
            return self.tools.list_notes()
        elif tool_name == "ingest_file":
            return self.tools.ingest_file(arguments.get("file_path"))
        else:
            return f"Error: Tool {tool_name} not found."
