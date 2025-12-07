# RAG Agent Project Documentation
> **Status**: � Production Ready (Phase: Optimization & Scaling)

## Technical Summary
**Project**: Real-time Video RAG Agent
**Role**: Full Stack AI Engineer
**Impact**: Engineered a low-latency RAG (Retrieval-Augmented Generation) pipeline capable of ingesting video inputs and facilitating semantic Q&A with <500ms response times.

**Core Architecture**:
-   **Backend**: Built an asynchronous event-driven API using **FastAPI** to handle long-running extraction tasks via **Server-Sent Events (SSE)**. Implemented custom generator patterns to stream transcription, chunking, and indexing progress updates to the client in real-time.
-   **RAG Pipeline**: orchestrated a vector search engine using **LangChain** and **Google Gemini 2.0 Flash**. Designed a recursive character splitting strategy (1000/200 overlap) to maximize context retention during semantic retrieval.
-   **Frontend**: Developed a robust **Next.js 16** interface with a custom React hook system to consume NDJSON streams without relying on external SDK overhead. Optimized the UI for instant feedback, successfully reducing perceived latency by removing blocking request patterns.
-   **Optimization**: Reduced operational costs by implementing model-tiering (fallback to Flash 1.5/2.0) and enforcing strict input constraints (5-minute video duration checks) via **yt-dlp** for robust metadata validation.
-   **Performance**: Implemented **Smart In-Memory Caching** to instantly restore previously processed videos upon page refresh, eliminating redundant API calls and processing time.

## Architecture

The system follows a modern client-server architecture with **Streaming Responses** for real-time feedback:

```mermaid
graph LR
    User[User] -->|URL| Frontend[Next.js Frontend]
    User -->|Chat| Frontend
    Frontend -->|POST /transcript (Stream)| Backend[FastAPI Backend]
    Frontend -->|POST /chat (Stream)| Backend
    Backend -->|Stream Events| Frontend
    Backend -->|Fetch| YouTube[YouTube API]
    Backend -->|Split| LangChain[LangChain Splitter]
    Backend -->|Embed| Gemini[Google Gemini API]
    Backend -->|Store| VectorDB[InMemory VectorStore]
    Backend -->|Search| VectorDB
    Backend -->|Generate| Gemini
```

### Components
1.  **Frontend (Next.js)**: A responsive web interface that consumes Server-Sent Events (SSE) to display real-time progress logs and streaming chat responses.
2.  **Backend (FastAPI)**: A high-performance Python API server dealing with long-running tasks via generators.
3.  **Extraction Engine**: Uses `youtube-transcript-api` to fetch subtitles.
4.  **Processing Pipeline**:
    *   **Text Splitting**: Breaks transcripts into 1000-character chunks (200 overlap).
    *   **Embedding**: Converts text chunks into 768-dimensional vectors using `models/text-embedding-004`.
    *   **Indexing**: Stores vectors in an in-memory database for retrieval.
5.  **RAG Engine**:
    *   **Search**: Finds relevant chunks.
    *   **Chat Agent**: Generates answers using `gemini-2.0-flash` (optimized for speed/quality) with a persona-based prompt.

## Tech Stack

### Backend
-   **Language**: Python 3.11+
-   **Framework**: FastAPI (Server), Uvicorn (ASGI) - *Now using StreamingResponse*
-   **AI & Logic**:
    -   `langchain`: Orchestration framework.
    -   `langchain-google-genai`: Google Gemini integration.
    -   `youtube-transcript-api`: Transcript fetching.
    -   `python-dotenv`: Environment variable management.

### Frontend
-   **Framework**: Next.js 16 (App Router)
-   **Language**: TypeScript
-   **Styling**: Tailwind CSS
-   **State Management**: React Hooks (Handling Streams)
-   **AI Integration**: Custom implementation using native `fetch` and `ReadableStream`.

## App Flow

1.  **User Input**: User enters a YouTube URL in the frontend.
2.  **Real-time Ingestion**:
    -   Frontend connects to `http://localhost:8000/transcript`.
    -   Backend streams status events: "Fetching...", "Splitting...", "Embedding...", "Indexing...".
    -   **Validation**: Videos longer than **5 minutes** are rejected to control costs/time.
    -   Frontend logs these events in a "System Logs" console.
3.  **Transcript Extraction**:
    -   Backend fetches subtitles (English or fallback).
4.  **Embedding Generation**:
    -   Chunks are sent to Google Gemini's Embedding API.
5.  **Vector Storage**: Vectors are stored in an `InMemoryVectorStore`.
6.  **Chat Interaction**:
    -   User asks a question.
    -   Backend streams updates: "Searching context...", "Found X chunks...", "Generating...".
    -   LLM (`gemini-2.0-flash`) generates an answer based *only* on the video content.
    -   Answer is streamed to the user's chat bubble.

## Setup Instructions

### Prerequisites
-   Python 3.11+
-   Node.js & Yarn
-   Google Cloud API Key (for Gemini)

### Backend Setup
1.  Navigate to the project root.
2.  Create a `.env` file with your API key:
    ```env
    GOOGLE_API_KEY="your_api_key_here"
    ```
3.  Install dependencies:
    ```bash
    pip3 install fastapi uvicorn langchain langchain-community langchain-google-genai youtube-transcript-api python-dotenv
    ```
4.  Run the server:
    ```bash
    python3 server.py
    ```
    *Server runs on port 8000.*

### Frontend Setup
1.  Navigate to `frontend/`:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm run dev
    ```
    *App runs on port 9100.*

## Usage
1.  Open [http://localhost:9100](http://localhost:9100).
2.  Paste a YouTube URL (e.g., `https://www.youtube.com/watch?v=jNQXAC9IVRw`).
3.  Click **"Train"**.
4.  Watch the **System Logs** for progress updates.
5.  Once complete, use the **Chat** interface to ask questions or summarize the video.

