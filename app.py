from flask import Flask, render_template, request, redirect, url_for
import ollama, subprocess, time, psutil

app = Flask(__name__)
chat_hist = []  # this is to save the what ever u talk with the llm

ollama_process = None  # process id


def kill_llama():
    global ollama_process
    if ollama_process:
        try:
            parent = psutil.Process(ollama_process.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            parent.wait()

            ollama_process = None
            print("ollama stopped")
        except psutil.NoSuchProcess:
            print("already killed")
    else:
        print("no ollama found")
        # to kill ollama dont ask what it does


@app.route('/', methods=["GET", "POST"])  # get and post for taking messages entered in the form in html
def index():
    if request.method == "POST":
        user_message = request.form["main"]
        chat_hist.append({"role": "user", "content": " " + user_message})  # saves the user message in a specified format

        response = ollama.chat(
            model="mistral",
            messages=chat_hist  # sends the message to the model
        )
        ai_response = response["message"]["content"]

        chat_hist.append({"role": "assistant", "content": ai_response})  # added to chat hist
        return redirect(url_for('index'))

    return render_template("index.html", chat_hist=chat_hist)


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
  
