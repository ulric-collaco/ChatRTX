# ChatRTX Clone

A local implementation inspired by NVIDIA's ChatRTX and Google's NotebookLM, providing conversational AI with document understanding capabilities.

## Overview

This project aims to create a self-hosted alternative to ChatRTX and NotebookLM, enabling users to chat with their documents locally while maintaining privacy and control over their data.

## Current Features

- **Local Chat Interface**: Simple Flask-based web application for conversational AI
- **Ollama Integration**: Leverages local Ollama models (currently Mistral) for chat responses
- **Document History**: Maintains conversation context across interactions
- **Privacy-First**: All processing happens locally, no data sent to external services

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │───▶│  Flask Backend  │───▶│  Ollama Local   │
│   (HTML/JS)     │    │   (Python)      │    │    Models       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Future: MCP   │
                       │   + RAG System  │
                       └─────────────────┘
```

## Planned Features

### 🔄 Model Context Protocol (MCP) Integration
- Host MCP server for extensible AI capabilities
- Plugin architecture for custom tools and data sources
- Standardized protocol for AI model interactions

### 📚 Retrieval Augmented Generation (RAG)
- Document ingestion and vectorization
- Semantic search across uploaded documents
- Context-aware responses based on document content
- Support for multiple document formats (PDF, DOCX, TXT, etc.)

### 🌐 Enhanced UI/UX
- Drag-and-drop document upload
- Real-time streaming responses
- Document source citations
- Chat history management

## Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.com/) installed and running
- Mistral model pulled in Ollama (`ollama pull mistral`)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ChatRtx
   ```

2. Install dependencies:
   ```bash
   pip install flask ollama psutil
   ```

3. Start the application:
   ```bash
   python app.py
   ```

4. Open your browser to `http://localhost:5000`

## Technology Stack

- **Backend**: Flask (Python)
- **AI Models**: Ollama (Local LLM hosting)
- **Frontend**: HTML, CSS, JavaScript
- **Planned**: 
  - Vector Database (ChromaDB/Qdrant)
  - MCP Server implementation
  - Document processing pipelines

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