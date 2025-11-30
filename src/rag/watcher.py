import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.rag.ingestor import Ingestor
from src.rag.vector_store import VectorStore

class NotesHandler(FileSystemEventHandler):
    def __init__(self, ingestor, vector_store):
        self.ingestor = ingestor
        self.vector_store = vector_store

    def on_created(self, event):
        if event.is_directory:
            return
        self.process(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self.process(event.src_path)

    def process(self, file_path):
        # Ignore temporary files
        if os.path.basename(file_path).startswith('~') or file_path.endswith('.tmp'):
            return
            
        # Wait a bit for file copy to complete
        time.sleep(1)
        try:
            self.ingestor.process_and_embed(file_path, self.vector_store)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

class FileWatcher:
    def __init__(self, watch_dir, vector_store, status_manager=None):
        self.watch_dir = watch_dir
        self.vector_store = vector_store
        self.ingestor = Ingestor(status_manager=status_manager)
        self.observer = Observer()

    def start(self):
        if not os.path.exists(self.watch_dir):
            os.makedirs(self.watch_dir)
            
        event_handler = NotesHandler(self.ingestor, self.vector_store)
        self.observer.schedule(event_handler, self.watch_dir, recursive=False)
        self.observer.start()
        print(f"Started watching {self.watch_dir}")

    def stop(self):
        self.observer.stop()
        self.observer.join()
