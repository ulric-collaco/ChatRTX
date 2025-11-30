# ChatRTX Clone

A local implementation inspired by NVIDIA's ChatRTX and Google's NotebookLM, providing conversational AI with document understanding capabilities.

## Overview

This project aims to create a self-hosted alternative to ChatRTX and NotebookLM, enabling users to chat with their documents locally while maintaining privacy and control over their data.

## Features

- **Local Chat Interface**: Flask-based web application.
- **Ollama Integration**: Uses local Ollama models (Gemma 3, Mistral, etc.).
- **RAG Pipeline**: Automatically ingests PDFs, Images, and Text files from the `notes/` directory.
- **Vector Database**: Uses ChromaDB for local vector storage.
- **MCP Server**: Implements a Model Context Protocol (MCP) gateway for tool calling.
- **File Watcher**: Automatically updates the index when files are added to `notes/`.
- **Privacy-First**: All processing happens locally.

## Architecture

```
d:\Coding\Projects\Python\ChatRtx\
  ├── app.py (Entry point)
  ├── requirements.txt
  ├── notes/ (Watched folder for study materials)
  ├── data/ (Vector DB persistence)
  ├── src/
  │   ├── llm/ (Ollama interaction)
  │   ├── mcp/ (Tool Gateway)
  │   ├── rag/ (Ingestion, Chunking, Vector DB)
  │   └── ui/
  ├── static/
  └── templates/
```

## Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.com/) installed and running.
- Pull a model: `ollama pull gemma3:4b` (or `mistral`, `llama3`, etc. - update `app.py` if needed).

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ChatRtx
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the application:
   ```bash
   python app.py
   ```

4. Open your browser to `http://localhost:5000`

5. Drop PDF, Image, or Text files into the `notes/` folder, or use the upload button in the UI.

## Technology Stack

- **Backend**: Flask (Python)
- **AI Models**: Ollama (Local LLM)
- **Vector DB**: ChromaDB
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **OCR**: Tesseract (via pytesseract)
- **PDF Parsing**: pypdf

## Inspiration

This project draws inspiration from:
- **NVIDIA ChatRTX**: Local RTX-powered AI chat with document understanding
- **Google NotebookLM**: Research-focused AI that can understand and discuss documents
- **Local-first AI**: Emphasis on privacy, control, and offline capabilities

## Contributing

This is an early-stage project. Contributions welcome for:
- RAG pipeline implementation
- MCP server development
- UI/UX improvements
- Document processing enhancements

## License

[Add your license here]

## Roadmap

- [x] Basic chat interface with Ollama
- [ ] Document upload and processing
- [ ] RAG implementation with vector search
- [ ] MCP server hosting
- [ ] Multi-model support
- [ ] Advanced document understanding
- [ ] Export/import chat sessions