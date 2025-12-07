from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from extract_transcript import extract_transcript_generator
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
import os
import json
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# -------------------------------------------------------------------------
# CORS Configuration
# Why this is needed: Browsers block requests between different origins (ports/domains) by default for security.
# We enable CORS (Cross-Origin Resource Sharing) to allow our frontend (port 9100) to talk to this backend (port 8000).
# -------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Security Note: In production, change this to your specific frontend domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to hold the vector store in memory.
# In a production app, this would be replaced by a persistent database/Vector DB instance (e.g., Pinecone, Chroma).
GLOBAL_VECTOR_STORE = None

class TranscriptRequest(BaseModel):
    url: str

class ChatRequest(BaseModel):
    message: str

# -------------------------------------------------------------------------
# Transcript Ingestion Endpoint
# Purpose: Fetches the video, extracts text, generates embeddings, and indexes them.
# Approach: Uses Server-Sent Events (SSE) (via StreamingResponse) to push real-time updates to the client.
#           This prevents the UI from freezing during long-running background tasks.
# -------------------------------------------------------------------------
@app.post("/transcript")
async def get_transcript(request: TranscriptRequest):
    global GLOBAL_VECTOR_STORE
    
    async def event_generator():
        global GLOBAL_VECTOR_STORE
        
        # Iterate over the generator from extract_transcript.py
        # Logic: We consume the generator's yields (status messages) and forward them to the client as events.
        #        When we receive the final 'InMemoryVectorStore' object, we update our global state.
        
        generator = extract_transcript_generator(request.url)
        
        for item in generator:
            if isinstance(item, str):
                # Valid JSON status message -> stream to client
                yield item
            elif isinstance(item, InMemoryVectorStore):
                # The vector store object -> update global state
                GLOBAL_VECTOR_STORE = item
                print("✅ Vector Store successfully stored in memory.")
            
            # Yield control to the event loop briefly to ensure efficient stream flushing
            await asyncio.sleep(0.01)

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

# -------------------------------------------------------------------------
# Chat Endpoint
# Purpose: Handles user questions by searching the indexed vector store.
# RAG Flow: 
#   1. Receive Query
#   2. Search Vector Store for top k similar chunks (Retrieval)
#   3. Construct Prompt with context + query (Augmentation)
#   4. Stream LLM response (Generation)
# -------------------------------------------------------------------------
@app.post("/chat")
async def chat(request: ChatRequest):
    global GLOBAL_VECTOR_STORE
    query = request.message
    print(f"💬 Received chat query: {query}")
    
    async def chat_generator():
        # Step 1: Notify UI regarding search status
        yield json.dumps({"status": "searching", "message": "Searching vector store for context..."}) + "\n"
        await asyncio.sleep(0.5) # Intentional small delay for UX pacing

        context = ""
        if GLOBAL_VECTOR_STORE:
            results = GLOBAL_VECTOR_STORE.similarity_search(query, k=5)
            context = "\n\n".join([doc.page_content for doc in results])
            yield json.dumps({"status": "found", "message": f"Found {len(results)} relevant chunks."}) + "\n"
        else:
            yield json.dumps({"status": "warning", "message": "No vector store found. Answering without context."}) + "\n"
        
        # Step 2: Notify UI regarding generation start
        yield json.dumps({"status": "generating", "message": "Generating response..."}) + "\n"
        
        # Step 3: LLM Generation
        try:
            # Using Gemini 2.0 Flash for balanced performance
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)
            
            # System Prompt: Defines the AI's persona and rules for using the retrieved context.
            template = """
            You are the professional AI persona of the speaker from the provided video transcript. 
            
            Context from video:
            {context}

            User Question:
            {question}

            Instructions:
            1. **Persona:** Speak in the first person ("I", "we") as if you are the creator of the video. Be professional, engaging, and helpful.
            2. **Summarization:** If the user asks to summarize the video, synthesize a comprehensive summary based *only* on the provided Context chunks.
            3. **General Knowledge:** If the user asks a general question (e.g., "accepted greeting", "who are you"), you may answer briefly to be polite, then steer them back to the video content.
            4. **Strict Context Limit:** For specific questions about the video's topic, stick STRICTLY to the "Context" provided. Do not invent information.
            5. **Refusal:** If the question is completely unrelated to the video or context (e.g., "Who won the 1998 World Cup?"), politely refuse by saying: 
               "I am not trained to answer that question as it is outside the context of this video."
            
            Answer:
            """
            
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | llm
            
            # Invoking the chain synchronously (LangChain invocation)
            response = chain.invoke({"question": query, "context": context})
            
            yield json.dumps({"status": "complete", "response": response.content}) + "\n"
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            yield json.dumps({"status": "error", "message": str(e)}) + "\n"

    return StreamingResponse(chat_generator(), media_type="application/x-ndjson")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

