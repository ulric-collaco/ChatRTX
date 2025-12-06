# ChatRTX Clone

A local implementation inspired by NVIDIA's ChatRTX and Google's NotebookLM, providing conversational AI with document understanding capabilities.
Implemented using Ollama

## Overview

This project aims to create a self-hosted alternative to ChatRTX and NotebookLM, enabling users to chat with their notes and study material locally while maintaining privacy and control over their data.

## How It Works




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
  ├── static/
  └── templates/
```

## Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.com/) installed and running.
- Pull a model: `ollama pull gemma3:4b` 

### Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the application:
   ```bash
   python app.py
   ```

3. Open your browser to `http://localhost:5000`

4. Drop PDF, Image, or Text files into the `notes/` folder, or use the upload button in the UI.

## Technology Stack

- **Backend**: Flask (Python)
- **AI Models**: Ollama (Local LLM)
- **Vector DB**: ChromaDB
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **OCR**: Tesseract (via pytesseract)
- **PDF Parsing**: pypdf

## Inspiration

I got inspired to make this project while having a conversation with my friend about ai and study. He asked me "make an ai where u can just dump notes and it will teach you that offline".I knew chatRtx existed but hadnt used it.This dropped me in a rabbit hole of trying to install it and figuring out my laptop cant run it and then trying to make my own solution




## Issues

The issues i can point out from initial testings are
1. UI
2. Dumb Replies

UI can be worked on but the second and primary issue can be fixed simply by using an bigger LLM
Bigger the LLM smarter the way it uses the tools and infomation being provided to it.
