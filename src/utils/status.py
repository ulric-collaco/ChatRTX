import queue
import json
import time

class StatusManager:
    def __init__(self):
        self.state = {
            "mode": "idle",
            "message": "",
            "progress": 0,
            "step": ""
        }
        self.listeners = []

    def update(self, mode=None, message=None, progress=None, step=None):
        if mode is not None:
            self.state["mode"] = mode
        if message is not None:
            self.state["message"] = message
        if progress is not None:
            self.state["progress"] = progress
        if step is not None:
            self.state["step"] = step
        
        self._notify_listeners()

    def set_idle(self):
        self.state = {
            "mode": "idle",
            "message": "",
            "progress": 0,
            "step": ""
        }
        self._notify_listeners()

    def _notify_listeners(self):
        # Create a data packet
        data = f"data: {json.dumps(self.state)}\n\n"
        # Send to all active listeners
        for q in self.listeners[:]:
            try:
                q.put_nowait(data)
            except queue.Full:
                self.listeners.remove(q)

    def listen(self):
        q = queue.Queue(maxsize=5)
        self.listeners.append(q)
        return q
