# ChatRTX Clone

A local implementation inspired by NVIDIA's ChatRTX and Google's NotebookLM, providing conversational AI with document understanding capabilities.
Implemented using Ollama

## Overview

This project aims to create a self-hosted alternative to ChatRTX and NotebookLM, enabling users to chat with their notes and study material locally while maintaining privacy and control over their data.

## How It Works

The system follows a two-step RAG (Retrieval-Augmented Generation) process:

1.  **Decision Phase**: The LLM analyzes the user's request to determine if it needs to search local notes, check chapter mappings, or (if enabled) search the internet.
2.  **Execution Phase**: The selected tool runs and returns data (e.g., text chunks from a PDF).
3.  **Generation Phase**: The LLM receives the tool's data and generates a final, grounded answer.

### Context Window & Tool Call Flow

The following diagram shows how the system prompt initializes the context, how chat history accumulates, and how a user message can trigger tool execution:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CONTEXT WINDOW (LLM Input)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ SYSTEM PROMPT (Initializes Context)                                   │  │
│  │ "You are a helpful assistant with access to the following tools:      │  │
│  │  - search_notes: Search through user's local notes                    │  │
│  │  - get_chapter: Retrieve chapter mappings                             │  │
│  │  When asked a question, decide if you need to use a tool..."          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ CHAT HISTORY (Accumulated Messages)                                   │  │
│  │ ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │ │ [USER]: "What is recursion?"                                    │   │  │
│  │ └─────────────────────────────────────────────────────────────────┘   │  │
│  │ ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │ │ [ASSISTANT]: <tool_call>search_notes("recursion")</tool_call>   │   │  │
│  │ └─────────────────────────────────────────────────────────────────┘   │  │
│  │ ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │ │ [TOOL RESULT]: "Recursion is when a function calls itself..."   │   │  │
│  │ └─────────────────────────────────────────────────────────────────┘   │  │
│  │ ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │ │ [ASSISTANT]: "Recursion is a programming concept where..."      │   │  │
│  │ └─────────────────────────────────────────────────────────────────┘   │  │
│  │ ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │ │ [USER]: "Explain BFS" ◄──── NEW USER MESSAGE                    │   │  │
│  │ └─────────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            OLLAMA LLM PROCESSING                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Reads system prompt → Understands available tools                  │  │
│  │ 2. Reviews chat history → Maintains conversation context              │  │
│  │ 3. Analyzes new message → "Explain BFS" needs local notes             │  │
│  │ 4. Decision: TRIGGER TOOL CALL                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        ┌───────────────────┐           ┌───────────────────────┐
        │   NO TOOL NEEDED  │           │   TOOL CALL NEEDED    │
        │   Direct Answer   │           │                       │
        └───────────────────┘           └───────────────────────┘
                                                    │
                                                    ▼
                              ┌─────────────────────────────────────────────┐
                              │              MCP TOOL SERVER                │
                              │  ┌───────────────────────────────────────┐  │
                              │  │ Tool: search_notes                    │  │
                              │  │ Args: {"query": "BFS"}                │  │
                              │  └───────────────────────────────────────┘  │
                              │                     │                       │
                              │                     ▼                       │
                              │  ┌───────────────────────────────────────┐  │
                              │  │ EXECUTION:                            │  │
                              │  │ 1. Embed query "BFS"                  │  │
                              │  │ 2. Search ChromaDB                    │  │
                              │  │ 3. Retrieve top-k chunks              │  │
                              │  └───────────────────────────────────────┘  │
                              │                     │                       │
                              │                     ▼                       │
                              │  ┌───────────────────────────────────────┐  │
                              │  │ RESULT: "BFS (Breadth-First Search)   │  │
                              │  │ is a graph traversal algorithm..."    │  │
                              │  └───────────────────────────────────────┘  │
                              └─────────────────────────────────────────────┘
                                                    │
                                                    ▼
                              ┌─────────────────────────────────────────────┐
                              │         RESULT INJECTED INTO CONTEXT        │
                              │  Context Window now includes:               │
                              │  - System Prompt                            │
                              │  - Previous Chat History                    │
                              │  - Tool Call + Tool Result  ◄── NEW         │
                              └─────────────────────────────────────────────┘
                                                    │
                                                    ▼
                              ┌─────────────────────────────────────────────┐
                              │      LLM GENERATES FINAL RESPONSE           │
                              │  "BFS is a graph traversal algorithm        │
                              │   that explores all neighbors at the        │
                              │   current depth before moving deeper..."    │
                              └─────────────────────────────────────────────┘
                                                    │
                                                    ▼
                              ┌─────────────────────────────────────────────┐
                              │   RESPONSE ADDED TO CHAT HISTORY            │
                              │   (Ready for next user message)             │
                              └─────────────────────────────────────────────┘
```

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
