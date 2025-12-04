# Frontend Documentation

## Overview
The frontend is a modern, responsive web application built with **Next.js 16** and **Tailwind CSS**. It serves as the user interface for the RAG Agent, allowing users to input video URLs and view processed transcripts.

## Tech Stack
-   **Framework**: Next.js (App Router)
-   **Language**: TypeScript
-   **Styling**: Tailwind CSS
-   **State Management**: React Hooks (`useState`)
-   **AI Integration**: Vercel AI SDK (`@ai-sdk/react` v2 / `ai` v5) - Manual input state management required.
-   **API Client**: Native `fetch` API

## Project Structure
```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx    # Global layout & font configuration
│   │   ├── page.tsx      # Main UI logic (Input form, API calls, Display)
│   │   └── globals.css   # Global styles & Tailwind directives
├── public/               # Static assets
├── next.config.ts        # Next.js configuration
├── tailwind.config.ts    # Tailwind configuration
└── package.json          # Dependencies & scripts
```

## Features
-   **Clean UI**: Minimalist design with a focus on readability.
-   **Real-time Feedback**:
    -   Loading states during API calls.
    -   Detailed console logs (Browser DevTools) tracking the request lifecycle (🚀, 🔗, 📡, ✅).
-   **Error Handling**: Graceful display of backend errors or network issues.
-   **Dark Mode**: Fully compatible with system dark mode settings.

## Development

### Running Locally
The frontend is configured to run on port **9100** to avoid conflicts with other services.

```bash
# Install dependencies
yarn install

# Start development server
npm run dev
```

Open [http://localhost:9100](http://localhost:9100) to view the app.

### Configuration
-   **Port**: Configured in `package.json` scripts: `"dev": "next dev -p 9100"`.
-   **API Endpoint**: Hardcoded to `http://localhost:8000/transcript` in `page.tsx`.
