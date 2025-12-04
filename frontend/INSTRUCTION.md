# Frontend Instructions & Workflow

## Workflow Status
- [x] Project Initialization (Next.js + Tailwind)
- [x] Basic UI Implementation (Input, Button, Transcript Display)
- [x] Backend Integration (Fetch API)
- [x] Vercel AI SDK Integration
  - [x] Install `ai` and `@ai-sdk/react`
  - [x] Implement `useChat` hook in `page.tsx`
  - [x] Fix import paths for SDK 5.0+
  - [x] Fix `useChat` input management (manual state) and `sendMessage` signature for SDK 5.0+

## Planning
1.  **Refine Chat UI**: Ensure the chat interface handles messages correctly.
2.  **Streaming Response**: Connect `useChat` to a backend endpoint that streams responses (currently backend only has `/transcript`).
3.  **RAG Integration**: Pass the transcript to the LLM context.

## Tech Stack Details
-   **Next.js 16**: Latest features including Server Actions (potential use).
-   **Vercel AI SDK**: Used for chat state management (`useChat`).
-   **Tailwind CSS**: For styling.
