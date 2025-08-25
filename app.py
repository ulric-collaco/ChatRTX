from flask import Flask, render_template, request, redirect, url_for, jsonify
import ollama, subprocess, time, psutil ,os,signal

app = Flask(__name__)
chat_hist = []  # this is to save the what ever u talk with the llm

ollama_process = None  # process id


# def kill_llama():
#     global ollama_process
#     if ollama_process:
#         try:
#             parent = psutil.Process(ollama_process.pid)
#             for child in parent.children(recursive=True):
#                 child.kill()
#             parent.kill()
#             parent.wait()

#             ollama_process = None
#             print("ollama stopped")
#         except psutil.NoSuchProcess:
#             print("already killed")
#     else:
#         print("no ollama found")
#         # to kill ollama dont ask what it does
def kill_llama():
    global ollama_process
    if ollama_process:
        try:
            # try a graceful terminate first
            if os.name == "nt":
                ollama_process.terminate()
            else:
                os.killpg(os.getpgid(ollama_process.pid), signal.SIGTERM)
            ollama_process.wait(timeout=5)
        except Exception:
            try:
                # force kill any children using psutil as before
                parent = psutil.Process(ollama_process.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
                parent.wait()
            except psutil.NoSuchProcess:
                pass
        finally:
            ollama_process = None
            print("ollama stopped")
    else:
        print("no ollama found")

# @app.route('/', methods=["GET", "POST"])  # get and post for taking messages entered in the form in html
# def index():
#     if request.method == "POST":
#         user_message = request.form["main"]
#         chat_hist.append({"role": "user", "content": " " + user_message})  # saves the user message in a specified format

#         response = ollama.chat(
#             model="gemma3:4b",
#             messages=chat_hist  # sends the message to the model
#         )
#         ai_response = response["message"]["content"]

#         chat_hist.append({"role": "assistant", "content": ai_response})  # added to chat hist
#         return redirect(url_for('index'))

#     return render_template("index.html", chat_hist=chat_hist)
@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_message = request.form.get("main", "").strip()
        if user_message:
            chat_hist.append({"role": "user", "content": user_message})
            response = ollama.chat(
                model="gemma3:4b",
                messages=chat_hist
            )
            ai_response = response.get("message", {}).get("content", "")
            chat_hist.append({"role": "assistant", "content": ai_response})
        return redirect(url_for('index'))

    return render_template("index.html", chat_hist=chat_hist)

@app.route('/api/message', methods=['POST'])
def api_message():
    data = request.get_json(silent=True) or {}
    user_message = (data.get('message') or "").strip()
    if not user_message:
        return jsonify({"ok": False, "error": "empty message"}), 400

    # append user message
    chat_hist.append({"role": "user", "content": user_message})

    # call model
    try:
        response = ollama.chat(model="gemma3:4b", messages=chat_hist)
        ai_response = response.get("message", {}).get("content", "")
    except Exception as e:
        ai_response = f"Model error: {e}"

    # append assistant message
    chat_hist.append({"role": "assistant", "content": ai_response})

    return jsonify({"ok": True, "assistant": ai_response})

@app.route('/end')
def end():
    kill_llama()
    return redirect(url_for('index'))


if __name__ == '__main__':
    ollama_process = subprocess.Popen(["ollama", "run", "mistral"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    print("ollama startin bg")

    try:
        print("Starting Flask server...")
        app.run(debug=True)
    finally:
        kill_llama()
        subprocess.run("powershell -Command Start-Process cmd -ArgumentList '/c taskkill /F /IM ollama.exe /T' -Verb runAs", shell=True)
  
