from src.rag.vector_store import VectorStore
from src.rag.ingestor import Ingestor
import os

class ToolSet:
    def __init__(self, vector_store: VectorStore, ingestor: Ingestor):
        self.vector_store = vector_store
        self.ingestor = ingestor

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
