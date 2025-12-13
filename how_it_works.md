# app.py

> this is the main flask app which serves the web interface and handles user interactions \

it initializes all the needed variables first 

---

### init_system

this function initially checks for internet connection using the `check_internet` function \

then it initializes the vector store , ingestor and llm from the `__init__.py` file in `src/mcp` 

### kill_ollama
this function kills the ollama process using os commands 

### get_system_prompt
this function is really important as it builds the system prompt for the llm \
the system prompt contains instructions for the llm on how to behave and use tools properly \

> **Note:** changing the prompt here will change how the model behaves and is crucial for the overall performance \

### process_message
this is the main function and only function used to process user messages \
this function first checks the chat history if theres none it makes a new one and appends the system prompt to it \
then it appends the user message to the chat history 

then it sends a chat to ollama and mentions the tool defintions in the same ollama function (ollama inherently supports tool calls now for some models) 

if the response contains a tool call dict (ollama protocol) it searches that dict for name and arguments 

if not the message simply gets appended to the chat history as a normal message and status is updated for the status manager 

the flow of tool call is as follows 
1. tool name and arguments are extracted from the response
2. `call_tool` function from `mcp/server.py` is called with tool name and arguments
fallback in place for malformed tool calls
3. the tool response is appended to the chat history as a tool message
4. status is updated for the status manager 


### routes

there are 2 main routes \
the end route \
the api routes 

the end route kills ollama using the function `kill_ollama` and then proceeds to kill flask app 

the api routes handle user queries and file uploads 