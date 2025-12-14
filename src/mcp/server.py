from src.mcp.tools import ToolSet
import json

class MCPServer:
    def __init__(self, tool_set: ToolSet, internet_enabled: bool = False):
        self.tools = tool_set
        self.tool_definitions = [
            {
                "name": "search_notes",
                "description": (
                    "Search the local knowledge base (vector database) for text chunks relevant to a specific query. "
                    "This is the primary tool for answering questions based on the user's uploaded documents. "
                    "Use this whenever the user asks about a concept, definition, algorithm, or topic that is likely contained in their notes. "
                    "Do NOT use this for general chit-chat or if the user explicitly asks for external information. \n\n"
                    "Examples:\n"
                    "- User: 'What is the definition of depreciation?' -> Tool Call: search_notes('definition of depreciation')\n"
                    "- User: 'Explain the difference between BFS and DFS' -> Tool Call: search_notes('BFS vs DFS difference')\n"
                    "- User: 'How does the transformer architecture work?' -> Tool Call: search_notes('transformer architecture mechanism')"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The specific topic, concept, or question to search for in the vector database."
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_notes",
                "description": (
                    "Retrieve a list of all filenames currently indexed in the knowledge base. "
                    "This tool checks the database and returns the names of all available documents (PDFs, images, text files). "
                    "Use this tool ONLY when the user explicitly asks what files are available, what notes they have uploaded, or requests an inventory of the system. "
                    "Do NOT call this tool automatically at the start of a conversation or if the user asks a question about the *content* of the notes. \n\n"
                    "Examples:\n"
                    "- User: 'What files do I have?' -> Tool Call: list_notes()\n"
                    "- User: 'List my notes' -> Tool Call: list_notes()\n"
                    "- User: 'Show me the uploaded documents' -> Tool Call: list_notes()"
                ),
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
                "description": (
                    "Use the Google Gemini API to generate comprehensive teaching notes, explanations, or tutorials on a topic from external knowledge. "
                    "This tool accesses the internet/LLM knowledge base rather than local files. "
                    "Use this tool ONLY in the following cases: "
                    "1) The user explicitly asks to 'teach' them a topic from scratch. "
                    "2) The user asks for information that is clearly not in their local notes (e.g., general world knowledge). "
                    "3) The local search_notes tool returned no results, and you need a fallback. \n\n"
                    "Examples:\n"
                    "- User: 'Teach me about Quantum Physics like I'm 5' -> Tool Call: search_internet('Quantum Physics ELI5')\n"
                    "- User: 'I don't have notes on this, can you explain Photosynthesis?' -> Tool Call: search_internet('Photosynthesis explanation')\n"
                    "- User: 'Generate a study guide for Calculus' -> Tool Call: search_internet('Calculus study guide')"
                ),
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
            
    def get_tool_definitions(self):
        return self.tool_definitions

    def call_tool(self, tool_name, arguments):
        """
        Execute a tool call.
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
        elif tool_name == "ingest_file":
            return self.tools.ingest_file(arguments.get("file_path"))
        else:
            return f"Error: Tool {tool_name} not found."
