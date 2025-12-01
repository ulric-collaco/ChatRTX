from src.rag.vector_store import VectorStore
from src.rag.ingestor import Ingestor
import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import json

load_dotenv()

class ToolSet:
    def __init__(self, vector_store: VectorStore, ingestor: Ingestor):
        self.vector_store = vector_store
        self.ingestor = ingestor
        
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini_model = None

    def search_internet(self, query: str) -> str:
        """
        Use Gemini API to generate comprehensive notes on a topic.
        """
        print(f"Tool Call: search_internet('{query}')")
        
        if not self.gemini_model:
            return "Error: Gemini API key not configured. Please check .env file."

        try:
            prompt = f"Provide comprehensive teaching notes on the topic: '{query}'. These notes should be suitable for a teacher to teach students. Include key definitions, examples, and structure."
            response = self.gemini_model.generate_content(prompt)
            return f"--- External Knowledge (Gemini) ---\n{response.text}"
        except Exception as e:
            return f"Error searching internet (Gemini): {str(e)}"

    def get_chapter_notes(self, chapter_identifier: str) -> str:
        """
        Retrieve notes for a specific chapter/module using the mapping.
        """
        print(f"Tool Call: get_chapter_notes('{chapter_identifier}')")
        try:
            with open("data/chapter_map.json", 'r') as f:
                mapping = json.load(f)
        except:
            return "Error: Chapter mapping not found."

        # Normalize identifier (e.g. "5" -> "module 5" or "chapter 5")
        target_key = chapter_identifier.lower().strip()
        
        # Try exact match
        files = mapping.get(target_key)
        
        # Try partial match (e.g. user said "5", map has "module 5")
        if not files:
            for key in mapping:
                if target_key in key.split(): # matches "5" in "module 5"
                    files = mapping[key]
                    break
        
        if not files:
            return f"No specific files found for '{chapter_identifier}'. Try searching for the topic name instead."

        # If files found, search specifically within them or return their content
        # For now, we'll return the filenames and suggest searching them, 
        # OR we can do a targeted search if the vector store supported filtering.
        # Since our vector store is simple, we will return the filenames and 
        # perform a broad search for the chapter name to get context.
        
        file_list = ", ".join(files)
        # Perform a search using the chapter name to get relevant chunks
        context = self.search_notes(chapter_identifier)
        
        return f"--- Chapter Files: {file_list} ---\n{context}"

    def search_notes(self, query: str) -> str:
        """
        Search the vector database for relevant notes.
        """
        print(f"Tool Call: search_notes('{query}')")
        results = self.vector_store.query(query)
        
        # Format results
        formatted_results = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                source = meta.get('filename', 'unknown')
                page = meta.get('page', 'unknown')
                formatted_results.append(f"--- Source: {source} (Page {page}) ---\n{doc}\n")
        
        if not formatted_results:
            return "No relevant notes found."
            
        return "\n".join(formatted_results)

    def list_notes(self) -> str:
        """
        List all available files in the index.
        """
        print("Tool Call: list_notes()")
        files = self.vector_store.get_all_files()
        if not files:
            return "No notes indexed."
        return "Available notes:\n" + "\n".join(f"- {f}" for f in files)

    def ingest_file(self, file_path: str) -> str:
        """
        Manually ingest a file.
        """
        print(f"Tool Call: ingest_file('{file_path}')")
        if not os.path.exists(file_path):
            return f"Error: File {file_path} not found."
            
        self.ingestor.process_and_embed(file_path, self.vector_store)
        return f"Successfully ingested {os.path.basename(file_path)}"

    def refresh_index(self) -> str:
        """
        Re-scan the notes directory.
        """
        # This would typically iterate over the notes dir and re-ingest
        # For now, we can just say it's not fully implemented or implement a simple scan
        return "Index refresh triggered (not fully implemented in this snippet)."
