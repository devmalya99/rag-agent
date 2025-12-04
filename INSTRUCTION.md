# Project Instructions & Workflow

## Project Goal
Build a RAG (Retrieval-Augmented Generation) Agent that can extract transcripts from YouTube videos, embed them using Google Gemini, and allow users to chat with the video content.

## Workflow Status
- [x] **Phase 1: Foundation**
  - [x] Backend: Transcript extraction API (FastAPI + youtube-transcript-api)
  - [x] Backend: Text splitting and embedding generation (LangChain + Gemini)
  - [x] Frontend: Basic UI to input URL and display transcript
- [x] **Phase 2: Chat Interface**
  - [x] Frontend: Integrate Vercel AI SDK (`useChat`)
  - [x] Frontend: Create chat UI components
- [x] **Phase 3: RAG Implementation**
  - [x] Backend: Create `/chat` endpoint for streaming responses (Standard JSON for now)
  - [x] Backend: Implement retrieval logic (query vector store)
  - [x] Backend: Generate answer using Gemini with retrieved context
  - [x] Frontend: Connect chat UI to backend `/chat` endpoint
- [ ] **Phase 4: Deployment & Version Control**
  - [ ] Fix GitHub CLI authentication (Switch to `devmalya99`)
  - [ ] Connect to fresh GitHub repository
  - [ ] Push initial code

## Planning
1.  **Backend Chat Endpoint**: Implement a streaming endpoint that accepts messages, retrieves relevant chunks, and generates a response.
2.  **Vector Store Persistence**: Currently using `InMemoryVectorStore`. Consider if persistence is needed (e.g., ChromaDB) or if per-session memory is sufficient.
3.  **Frontend Streaming**: Ensure the frontend handles streaming responses correctly.

## Tech Stack
-   **Backend**: Python, FastAPI, LangChain, Google Gemini API
-   **Frontend**: Next.js, TypeScript, Tailwind CSS, Vercel AI SDK
