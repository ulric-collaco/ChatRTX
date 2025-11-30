import chromadb
from chromadb.utils import embedding_functions
import os

class VectorStore:
    def __init__(self, persistence_path="data/chroma_db", collection_name="chatrtx_notes"):
        self.client = chromadb.PersistentClient(path=persistence_path)
        
        # Use a local embedding model
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def add_documents(self, documents, metadatas, ids):
        """
        Add documents to the vector store.
        documents: list of strings
        metadatas: list of dicts
        ids: list of strings
        """
        if not documents:
            return
            
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query_text, n_results=5):
        """
        Query the vector store.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results

    def delete_document(self, filename):
        """
        Delete all chunks associated with a filename.
        """
        self.collection.delete(
            where={"filename": filename}
        )

    def get_all_files(self):
        """
        Get a list of all unique filenames in the store.
        """
        # This is a bit expensive in Chroma, but manageable for personal use
        # We fetch just metadata to list files
        result = self.collection.get(include=['metadatas'])
        files = set()
        for meta in result['metadatas']:
            if meta and 'filename' in meta:
                files.add(meta['filename'])
        return list(files)

    def reset(self):
        self.client.reset()
