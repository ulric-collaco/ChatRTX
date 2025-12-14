from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
import ollama
import subprocess
import time
import psutil
import os
import signal
import threading

# Import our new modules
from src.rag.vector_store import VectorStore
from src.rag.ingestor import Ingestor
from src.rag.watcher import FileWatcher
from src.mcp.tools import ToolSet
from src.mcp.server import MCPServer
from src.utils.status import StatusManager

app = Flask(__name__)
chat_hist = []

import requests

# Global components
vector_store = None
ingestor = None
file_watcher = None
tool_set = None
mcp_server = None
ollama_process = None
status_manager = None
INTERNET_AVAILABLE = False

MODEL_NAME = "llama3.1:8b-instruct-q4_K_M"

def check_internet():
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except:
        return False

def get_system_prompt():
    internet_status = "ONLINE" if INTERNET_AVAILABLE else "OFFLINE"

    prompt = f"""
You are ChatRTX, a helpful AI assistant that answers questions using local knowledge from uploaded documents.

SYSTEM STATUS: {internet_status}

═══════════════════════════════════════════════════════════════════════════════
AVAILABLE TOOLS
═══════════════════════════════════════════════════════════════════════════════

🔧 TOOL 1: list_notes()
   Returns: List of all uploaded document filenames
   
   USE THIS TOOL WHEN:
   ✓ User asks "what notes/files/documents do you have?"
   ✓ User asks "list my notes" or "show my files"
   ✓ User asks "what have I uploaded?"
   
   DO NOT USE when:
   ✗ User asks to explain/teach/summarize CONTENT from notes
   ✗ User mentions "my notes" but wants content (use search_notes instead)
   
   Examples of CORRECT usage:
   • "what notes do u have rn" → list_notes()
   • "list all my files" → list_notes()
   • "show uploaded documents" → list_notes()
   
   Examples of INCORRECT usage:
   • "teach me X from my notes" → DO NOT use list_notes, use search_notes instead
   • "explain Y according to my notes" → DO NOT use list_notes, use search_notes instead

🔧 TOOL 2: search_notes(query)
   Parameter: query (string) - the topic/concept to search for
   Returns: Relevant text chunks from uploaded documents
   
   USE THIS TOOL WHEN:
   ✓ User asks to explain/teach/define a concept
   ✓ User asks "what is X?" or "how does Y work?"
   ✓ User asks about chapters/modules (e.g., "chapter 5", "module 2")
   ✓ User says "according to my notes" or "from my notes" followed by a topic
   ✓ User asks for summaries or information extraction
   
   Query construction:
   • For topic: search_notes("depreciation")
   • For chapter: search_notes("chapter 5") or search_notes("module 2")
   • For teaching: search_notes("impairment")
   
   Examples of CORRECT usage:
   • "what is BFS?" → search_notes("BFS breadth first search")
   • "explain hashing" → search_notes("hashing")
   • "teach me impairment from my notes" → search_notes("impairment")
   • "summarize chapter 5" → search_notes("chapter 5")
   • "what is depreciation according to my notes?" → search_notes("depreciation")
"""

    if INTERNET_AVAILABLE:
        prompt += """
🔧 TOOL 3: search_internet(query)
   Parameter: query (string) - the topic to generate teaching notes for
   Returns: Comprehensive teaching content from external AI model
   
   USE THIS TOOL WHEN:
   ✓ search_notes returned "No relevant notes found"
   ✓ User explicitly asks for information beyond their notes
   ✓ User says "teach me" and local notes are insufficient
   
   DO NOT USE as first choice - always try search_notes first.
   
   Examples:
   • After search_notes fails: search_internet("quantum mechanics")
   • User asks: "explain something not in my notes" → search_internet(topic)
"""

    prompt += f"""

═══════════════════════════════════════════════════════════════════════════════
DECISION LOGIC (Follow this EXACTLY)
═══════════════════════════════════════════════════════════════════════════════

STEP 1: Analyze user's intent

Is the user asking WHICH files exist?
├─ YES → Call list_notes()
└─ NO → Continue to Step 2

STEP 2: Does the user want CONTENT/information about a topic?
├─ YES → Call search_notes("topic name")
│   └─ If result is empty and internet is {internet_status}:
│       └─ Call search_internet("topic name") for external help
└─ NO → Answer directly without tools

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════════════════════

1. TOOL CALLING FORMAT:
   When calling a tool, you MUST use this exact structure:
   - Tool name must be exactly: "list_notes" OR "search_notes" OR "search_internet"
   - Arguments must match the parameter names shown above
   
2. GROUNDING:
   - NEVER invent filenames, document content, or claim notes exist
   - Only report what tools return
   - If search_notes returns nothing, say "No relevant notes found"
   
3. OUTPUT FORMAT (CRITICAL):
   ⚠️  NEVER describe which tool you used or how you found the answer
   ⚠️  NEVER say "I used TOOL X" or "I searched" or "I called"
   ✓  Just provide the answer directly using the tool results
   ✓  For list_notes: list the files in a simple bullet format
   ✓  For search_notes: answer the question using the retrieved content
   ✓  Cite source filenames naturally (e.g., "According to [filename]...")
   
4. RESPONSE STYLE:
   - Be direct and concise
   - When teaching, organize information clearly with headings/bullets
   - Use the content from tools, don't narrate your process
   
5. TOOL SELECTION:
   - list_notes: ONLY for "what files do you have" questions
   - search_notes: PRIMARY tool for all content questions
   - search_internet: FALLBACK when local notes insufficient

═══════════════════════════════════════════════════════════════════════════════

Now respond to the user's message following these rules exactly.
DO NOT describe your process. Just answer the question using tool results.
"""

    return {
        "role": "system",
        "content": prompt
    }

def init_system():
    global vector_store, ingestor, file_watcher, tool_set, mcp_server, status_manager, INTERNET_AVAILABLE
    
    print("Checking internet connectivity...")
    INTERNET_AVAILABLE = check_internet()
    print(f"Internet Status: {'Online' if INTERNET_AVAILABLE else 'Offline'}")

    print("Initializing RAG system...")
    # Ensure directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("notes", exist_ok=True)
    
    status_manager = StatusManager()
    vector_store = VectorStore(persistence_path="data/chroma_db")
    ingestor = Ingestor(status_manager=status_manager)
    
    # Start file watcher
    file_watcher = FileWatcher(watch_dir="notes", vector_store=vector_store, status_manager=status_manager)
    file_watcher.start()
    
    # Setup MCP
    tool_set = ToolSet(vector_store, ingestor)
    mcp_server = MCPServer(tool_set, internet_enabled=INTERNET_AVAILABLE)
    print("System initialized.")

def kill_llama():
    global ollama_process
    print("Attempting to kill Ollama...")
    
    # First, try to kill the specific process we started
    if ollama_process:
        try:
            if os.name == "nt":
                ollama_process.terminate()
            else:
                os.killpg(os.getpgid(ollama_process.pid), signal.SIGTERM)
            ollama_process.wait(timeout=2)
        except Exception as e:
            print(f"Error terminating process: {e}")
        finally:
            ollama_process = None

    # Second, force kill any lingering ollama.exe processes on Windows
    if os.name == "nt":
        try:
            subprocess.run("taskkill /F /IM ollama.exe /T", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Force killed ollama.exe")
        except Exception as e:
            print(f"Error force killing ollama: {e}")

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_message = request.form.get("main", "").strip()
        if user_message:
            process_message(user_message)
        return redirect(url_for('index'))

    return render_template("index.html", chat_hist=chat_hist)

@app.route('/api/status/stream')
def stream_status():
    def event_stream():
        q = status_manager.listen()
        try:
            while True:
                data = q.get()
                yield data
        except GeneratorExit:
            status_manager.listeners.remove(q)
            
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/api/message', methods=['POST'])
def api_message():
    data = request.get_json(silent=True) or {}
    user_message = (data.get('message') or "").strip()
    if not user_message:
        return jsonify({"ok": False, "error": "empty message"}), 400

    ai_response = process_message(user_message)
    return jsonify({"ok": True, "assistant": ai_response})

@app.route('/api/clear', methods=['POST'])
def api_clear():
    global chat_hist
    chat_hist = []
    # Re-initialize with system prompt
    chat_hist.append(get_system_prompt())
    return jsonify({"ok": True})

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return jsonify({"ok": False, "error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"ok": False, "error": "No selected file"}), 400
    
    if file:
        filename = file.filename
        # Secure filename is good practice, but for local personal use, we might want to keep original names
        # from werkzeug.utils import secure_filename
        # filename = secure_filename(file.filename)
        save_path = os.path.join("notes", filename)
        
        # Update status to uploading
        status_manager.update(mode="processing", message=f"Uploading {filename}...", progress=0, step="upload")
        
        file.save(save_path)
        
        # Notify the chat history about the new file
        global chat_hist
        chat_hist.append({
            "role": "system", 
            "content": f"System Notification: User has uploaded '{filename}'. It is currently being indexed and will be available for search shortly."
        })
        
        return jsonify({"ok": True, "message": f"File {filename} uploaded successfully. Indexing will start shortly."})

def process_message(user_message):
    global chat_hist
    if not chat_hist:
        chat_hist.append(get_system_prompt())

    chat_hist.append({"role": "user", "content": user_message})
    
    status_manager.update(mode="thinking", message="AI is thinking...", progress=0)
    
    try:
        # First call to LLM with tools
        print(f"Sending request to {MODEL_NAME} with tools...")
        response = ollama.chat(
            model=MODEL_NAME,
            messages=chat_hist,
            tools=mcp_server.get_tool_definitions()
        )
        
        message = response.get("message", {})
        
        # Check if the model wants to call a tool
        if message.get("tool_calls"):
            print(f"Model requested {len(message['tool_calls'])} tool calls.")
            # Add the model's message (with tool calls) to history
            chat_hist.append(message)
            
            for tool_call in message["tool_calls"]:
                function_name = tool_call["function"].get("name")
                arguments = tool_call["function"].get("arguments") or {}
                
                if not function_name:
                    # Fallback for malformed tool calls
                    last_user_raw = chat_hist[-2]["content"] if len(chat_hist) >= 2 else ""
                    last_user_msg = last_user_raw.lower()

                    # 1) Explicit inventory requests ONLY -> list_notes
                    # Must be asking WHICH files exist, not CONTENT from files
                    inventory_only_markers = [
                        "what notes do", "what files do", "what documents do",
                        "list notes", "list files", "list documents",
                        "show notes", "show files", "show documents",
                        "which notes", "which files"
                    ]
                    # Exclude if asking for content
                    content_markers = ["teach", "explain", "what is", "how", "summarize", "according to", "from my notes"]
                    
                    is_inventory = any(m in last_user_msg for m in inventory_only_markers)
                    is_content = any(m in last_user_msg for m in content_markers)
                    
                    if is_inventory and not is_content:
                        print("Warning: Empty tool name. Inferring 'list_notes' from inventory request")
                        function_name = "list_notes"
                        arguments = {}

                    # 2) Teaching/explanation requests -> search_notes (or search_internet as fallback)
                    elif is_content:
                        print("Warning: Empty tool name. Inferring 'search_notes' from content request")
                        function_name = "search_notes"
                        # Try to extract topic from user message
                        if isinstance(arguments, dict) and arguments.get("query"):
                            # Keep existing query if provided
                            pass
                        else:
                            # Use the user message as query
                            arguments = {"query": last_user_raw}

                    # 3) Default -> search_notes
                    else:
                        print("Warning: Empty tool name. Defaulting to 'search_notes'")
                        function_name = "search_notes"
                        arguments = {"query": last_user_raw} if not (isinstance(arguments, dict) and arguments.get("query")) else arguments

                status_manager.update(mode="tool_call", message=f"Using tool: {function_name}", progress=50)
                print(f"Executing tool: {function_name} with args: {arguments}")
                
                try:
                    tool_result = mcp_server.call_tool(function_name, arguments)
                except Exception as e:
                    tool_result = f"Error executing tool {function_name}: {str(e)}"
                
                # Add tool result to history
                chat_hist.append({
                    "role": "tool",
                    "content": str(tool_result),
                    "name": function_name
                })
            # Second call to LLM to get final answer
            print("Sending follow-up request to LLM...")
            status_manager.update(mode="thinking", message="Generating final response...", progress=75)
            final_response = ollama.chat(
                model=MODEL_NAME,
                messages=chat_hist
            )
            ai_response = final_response.get("message", {}).get("content", "")
        else:
            ai_response = message.get("content", "")

    except Exception as e:
        print(f"Error in chat loop: {e}")
        ai_response = f"I encountered an error: {str(e)}"
        # Fallback: try without tools if it failed (e.g. model doesn't support tools)
        if "does not support tools" in str(e):
             try:
                response = ollama.chat(model=MODEL_NAME, messages=chat_hist)
                ai_response = response.get("message", {}).get("content", "")
             except:
                 pass
    
    if not (ai_response or "").strip():
        ai_response = "I couldn't generate a response just now. Please try again."

    status_manager.set_idle()
    chat_hist.append({"role": "assistant", "content": ai_response})
    return ai_response

@app.route('/end')
def end():
    print("Ending session...")
    if file_watcher:
        file_watcher.stop()
    
    # Kill Ollama
    kill_llama()
    
    # Kill the Flask server itself
    # This is a bit aggressive but ensures everything stops
    os.kill(os.getpid(), signal.SIGINT)
    
    return "Session ended. You can close this tab."

if __name__ == '__main__':
    # Start Ollama in background (optional, if user doesn't have it running)
    # We use 'serve' if possible, or just 'run' to keep it alive.
    # Assuming user has installed ollama.
    try:
        ollama_process = subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Ollama started in background (serve mode)")
    except FileNotFoundError:
        print("Ollama executable not found. Please ensure Ollama is installed and in PATH.")
    
    time.sleep(2) # Wait for Ollama to start
    
    init_system()

    try:
        print("Starting Flask server...")
        app.run(debug=True, use_reloader=False) # use_reloader=False to avoid double init
    finally:
        if file_watcher:
            file_watcher.stop()
        kill_llama()


