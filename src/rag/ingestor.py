import os
import pypdf
import pytesseract
from PIL import Image
import uuid
import time
import json
import re

class Ingestor:
    def __init__(self, chunk_size=1000, chunk_overlap=200, status_manager=None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.status_manager = status_manager
        self.map_file = "data/chapter_map.json"
        self._ensure_map_file()

    def _ensure_map_file(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.map_file):
            with open(self.map_file, 'w') as f:
                json.dump({}, f)

    def _update_map(self, filename, content):
        """
        Extract chapter/module info and update the map.
        """
        try:
            with open(self.map_file, 'r') as f:
                mapping = json.load(f)
        except:
            mapping = {}

        # 1. Check filename
        name_lower = filename.lower()
        patterns = [
            r"(module|chapter|unit)\s*(\d+)",
            r"(module|chapter|unit)-(\d+)",
            r"(module|chapter|unit)_(\d+)",
            # Add more flexible patterns
            r"(module|chapter|unit)\s*([ivx]+)", # Roman numerals
            r"(module|chapter|unit)\s*([a-z])\b" # Single letters
        ]
        
        found_keys = []
        for pat in patterns:
            match = re.search(pat, name_lower)
            if match:
                # Normalize key
                prefix = match.group(1)
                val = match.group(2)
                key = f"{prefix} {val}" 
                found_keys.append(key)

        # 2. Check first 2000 chars of content if no filename match
        # Also check for "Topic: X" or "Subject: Y"
        if not found_keys and content:
            intro = content[:2000].lower()
            
            # Standard patterns in content
            for pat in patterns:
                match = re.search(pat, intro)
                if match:
                    prefix = match.group(1)
                    val = match.group(2)
                    key = f"{prefix} {val}"
                    found_keys.append(key)
            
            # If still nothing, try to extract a title from the first few lines
            if not found_keys:
                lines = [l.strip() for l in intro.split('\n') if l.strip()]
                if lines:
                    # Use the first non-empty line as a potential "topic" key
                    # This is a heuristic: "Graph Theory" -> "topic: graph theory"
                    # We limit it to short titles (e.g. < 50 chars)
                    title_candidate = lines[0]
                    if len(title_candidate) < 50:
                        # Clean it up
                        clean_title = re.sub(r'[^\w\s]', '', title_candidate)
                        key = f"topic: {clean_title}"
                        found_keys.append(key)

        # Update mapping
        if found_keys:
            for key in found_keys:
                if key not in mapping:
                    mapping[key] = []
                if filename not in mapping[key]:
                    mapping[key].append(filename)
            
            with open(self.map_file, 'w') as f:
                json.dump(mapping, f, indent=2)
            
            print(f"Mapped {filename} to {found_keys}")
        else:
            # Fallback: Map to filename itself as a topic
            # e.g. "Graph Theory.pdf" -> "topic: graph theory"
            clean_name = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
            key = f"topic: {clean_name.lower()}"
            
            if key not in mapping:
                mapping[key] = []
            if filename not in mapping[key]:
                mapping[key].append(filename)
            
            with open(self.map_file, 'w') as f:
                json.dump(mapping, f, indent=2)
            print(f"Mapped {filename} to fallback {key}")

    def _update_status(self, mode, message, progress=0, step=""):
        if self.status_manager:
            self.status_manager.update(mode=mode, message=message, progress=progress, step=step)

    def load_file(self, file_path):
        """
        Load a file and return text content.
        Supports .pdf, .png, .jpg, .jpeg, .txt
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return self._process_pdf(file_path)
        elif ext in ['.png', '.jpg', '.jpeg']:
            return self._process_image(file_path)
        elif ext == '.txt':
            return self._process_text(file_path)
        else:
            print(f"Unsupported file type: {ext}")
            return []

    def _process_pdf(self, file_path):
        text_chunks = []
        try:
            reader = pypdf.PdfReader(file_path)
            full_text = ""
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if not text.strip():
                    # Try OCR if text extraction fails (scanned PDF)
                    # This is a simplified approach; for robust OCR on PDF, 
                    # one might need pdf2image -> pytesseract
                    pass 
                
                # Simple page-level metadata
                page_text = text
                chunks = self._chunk_text(page_text)
                for chunk in chunks:
                    text_chunks.append({
                        "text": chunk,
                        "metadata": {
                            "source": file_path,
                            "filename": os.path.basename(file_path),
                            "page": i + 1
                        }
                    })
        except Exception as e:
            print(f"Error processing PDF {file_path}: {e}")
        return text_chunks

    def _process_image(self, file_path):
        try:
            text = pytesseract.image_to_string(Image.open(file_path))
            chunks = self._chunk_text(text)
            return [{
                "text": chunk,
                "metadata": {
                    "source": file_path,
                    "filename": os.path.basename(file_path),
                    "page": 1
                }
            } for chunk in chunks]
        except Exception as e:
            print(f"Error processing image {file_path}: {e}")
            return []

    def _process_text(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            chunks = self._chunk_text(text)
            return [{
                "text": chunk,
                "metadata": {
                    "source": file_path,
                    "filename": os.path.basename(file_path),
                    "page": 1
                }
            } for chunk in chunks]
        except Exception as e:
            print(f"Error processing text file {file_path}: {e}")
            return []

    def _chunk_text(self, text):
        """
        Simple sliding window chunker.
        """
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap
            
        return chunks

    def process_and_embed(self, file_path, vector_store):
        """
        Process a file and add it to the vector store.
        """
        filename = os.path.basename(file_path)
        print(f"Processing {file_path}...")
        self._update_status("processing", f"Starting ingestion for {filename}", 10, "init")
        
        chunks_data = self.load_file(file_path)
        
        if not chunks_data:
            print(f"No text found in {file_path}")
            self._update_status("processing", f"No text found in {filename}", 100, "error")
            time.sleep(2)
            self._update_status("idle", "")
            return

        self._update_status("processing", f"Chunking {filename}...", 40, "chunking")
        
        documents = [item['text'] for item in chunks_data]
        metadatas = [item['metadata'] for item in chunks_data]
        ids = [f"{filename}_{i}_{str(uuid.uuid4())[:8]}" for i in range(len(documents))]
        
        # Remove existing docs for this file to avoid duplicates
        vector_store.delete_document(filename)
        
        # Update chapter map
        full_text = " ".join(documents)
        self._update_map(filename, full_text)
        
        self._update_status("processing", f"Embedding {len(documents)} chunks...", 70, "embedding")
        vector_store.add_documents(documents, metadatas, ids)
        
        print(f"Added {len(documents)} chunks to vector store for {file_path}")
        self._update_status("complete", f"Successfully processed {filename}", 100, "complete")
        
        # Wait a moment so user sees the completion, then go idle
        time.sleep(3)
        self._update_status("idle", "")

    def sync_existing_files(self, notes_dir, vector_store):
        """
        Scan the notes directory and ensure all files are indexed and mapped.
        """
        print(f"Syncing files in {notes_dir}...")
        if not os.path.exists(notes_dir):
            return

        # Get files on disk
        disk_files = [f for f in os.listdir(notes_dir) if os.path.isfile(os.path.join(notes_dir, f))]
        
        # Get files in vector store
        indexed_files = set(vector_store.get_all_files())
        
        for filename in disk_files:
            file_path = os.path.join(notes_dir, filename)
            
            # 1. Always try to update the map (it's fast and idempotent)
            # We try to read a bit of content for better mapping if possible
            content_head = ""
            try:
                ext = os.path.splitext(filename)[1].lower()
                if ext == '.txt':
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content_head = f.read(1000)
                elif ext == '.pdf':
                    # Quick attempt to read first page text for mapping
                    try:
                        reader = pypdf.PdfReader(file_path)
                        if len(reader.pages) > 0:
                            content_head = reader.pages[0].extract_text()[:1000]
                    except:
                        pass
            except:
                pass
            
            self._update_map(filename, content_head)

            # 2. Ingest if missing from vector store
            if filename not in indexed_files:
                print(f"Found unindexed file {filename}, ingesting...")
                self.process_and_embed(file_path, vector_store)
            else:
                print(f"File {filename} is already indexed.")
