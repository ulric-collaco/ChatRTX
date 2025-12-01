from src.mcp.tools import ToolSet
import json

class MCPServer:
    def __init__(self, tool_set: ToolSet, internet_enabled: bool = False):
        self.tools = tool_set
        self.tool_definitions = [
            {
                "name": "search_notes",
                "description": "Search the knowledge base for text chunks relevant to a specific query. Use this only when the user asks a question that requires external information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The specific topic or question to search for."
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_notes",
                "description": "Get a list of filenames currently in the knowledge base. Use this only when the user asks what files are available.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        if internet_enabled:
            self.tool_definitions.append({
                "name": "search_internet",
                "description": "Use Gemini API to generate comprehensive teaching notes on a topic. Use this ONLY if the user asks for external information, 'teaching', or if local notes are insufficient.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The topic to generate notes for."
                        }
                    },
                    "required": ["query"]
                }
            })
            
        self.tool_definitions.append({
            "name": "get_chapter_notes",
            "description": "Retrieve notes for a specific chapter, module, or unit. Use this when the user mentions 'Chapter X', 'Module Y', or just a number in a learning context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chapter_identifier": {
                        "type": "string",
                        "description": "The identifier, e.g., 'Module 5', 'Chapter 3', or just '5'."
                    }
                },
                "required": ["chapter_identifier"]
            }
        })

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
        elif tool_name == "search_internet":
            return self.tools.search_internet(arguments.get("query"))
        elif tool_name == "get_chapter_notes":
            return self.tools.get_chapter_notes(arguments.get("chapter_identifier"))
        elif tool_name == "ingest_file":
            return self.tools.ingest_file(arguments.get("file_path"))
        else:
            return f"Error: Tool {tool_name} not found."
