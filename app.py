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

# Global components
vector_store = None
ingestor = None
file_watcher = None
tool_set = None
mcp_server = None
ollama_process = None
status_manager = None

MODEL_NAME = "llama3.1:8b-instruct-q4_K_M" # DeepSeek-R1 can struggle with tool schemas, switching to Llama 3.1


def init_system():
    global vector_store, ingestor, file_watcher, tool_set, mcp_server, status_manager
    
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
    mcp_server = MCPServer(tool_set)
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
        return jsonify({"ok": True, "message": f"File {filename} uploaded successfully. Indexing will start shortly."})

def process_message(user_message):
    global chat_hist
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
                arguments = tool_call["function"].get("arguments")
                
                if not function_name:
                    print(f"Error: Model generated tool call with empty name. Args: {arguments}")
                    status_manager.update(mode="error", message="Model tool error", progress=0)
                    continue

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


