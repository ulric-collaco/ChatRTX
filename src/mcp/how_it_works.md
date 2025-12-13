# server.py

> this is the main file which makes the mcp \
> this follows the protocol rules and implements tool call using \
> name desciption paratmeters and more 

> **Tip:** descriptions can be modified to change how the model works

---

### self.tools.definitions 
this basiclly holds all the tool definitions for the model to use from the `tools.py` file \
this is a speicial dict which follows the protocol

### self.tools.call_tool
this function is used whenever a tool is called by the model \
it takes 2 arguments tool name and arguments for that tool 

---

# tools.py

> this file contains the actual tool implementations of the tools mentioned in `server.py` \
> each function is basically the tool 

### __init__.py
this loads vector store , ingestor and gemini llm 

### each tool is defined as a fucntion with specific arguments as needed

