# Frontend Documentation

## Overview
The frontend is a modern, responsive web application built with **Next.js 16** and **Tailwind CSS**. It interacts with the FastAPI backend using **Server-Sent Events (NDJSON streaming)** to provide real-time updates during transcription and chat generation.

## Tech Stack
-   **Framework**: Next.js (App Router)
-   **Language**: TypeScript
-   **Styling**: Tailwind CSS
-   **State Management**: React Hooks (`useState`, `useRef`)
-   **Streaming**: Native `fetch` API + `ReadableStream` (Handling NDJSON streams)
-   **Markdown Rendering**: `react-markdown` with `tailwindcss-typography` (Prose)
-   **Icons**: Standard UTF-8 / Tailwind utilities

## Project Structure
```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx    # Global layout & font configuration
│   │   ├── page.tsx      # Main UI logic (Streaming consumer, Logs, Chat)
│   │   └── globals.css   # Global styles & Tailwind directives
├── public/               # Static assets
├── next.config.ts        # Next.js configuration
├── tailwind.config.ts    # Tailwind configuration
└── package.json          # Dependencies & scripts
```

## Features
-   **Real-time System Logs**: Displays backend progress (fetching, splitting, embeddings) as a scrolling log.
-   **Streaming Chat**: Chat responses appear token-by-token (or chunk-by-chunk) for a responsive feel.
-   **Status Indicators**: Visual cues for "Thinking...", "Searching...", and "Generating...".
-   **Clean UI**: Dark mode compatible, minimalist design.

## Development

### Running Locally
The frontend is configured to run on port **9100** to avoid conflicts with instruction services.

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:9100](http://localhost:9100) to view the app.

### Configuration
-   **Port**: Configured in `package.json` scripts: `"dev": "next dev -p 9100"`.
-   **API Endpoint**: Hardcoded to `http://localhost:8000` in `page.tsx`.

