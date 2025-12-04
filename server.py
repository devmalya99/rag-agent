from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from extract_transcript import extract_transcript
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to hold the vector store in memory
GLOBAL_VECTOR_STORE = None

class TranscriptRequest(BaseModel):
    url: str

class ChatRequest(BaseModel):
    message: str

class SearchRequest(BaseModel):
    query: str
    k: int = 4

@app.post("/transcript")
async def get_transcript(request: TranscriptRequest):
    global GLOBAL_VECTOR_STORE
    result = extract_transcript(request.url)
    
    # Check if result is an error string (old behavior fallback check)
    if isinstance(result, str) and result.startswith("Error:"):
        raise HTTPException(status_code=400, detail=result)
    
    # Unpack tuple (now 3 values)
    transcript, splits, vector_store = result
    
    # Double check for error in transcript string
    if transcript.startswith("Error:"):
        raise HTTPException(status_code=400, detail=transcript)

    # Store the vector store globally
    if vector_store:
        GLOBAL_VECTOR_STORE = vector_store
        print("✅ Vector Store successfully stored in memory.")
    else:
        print("⚠️ No Vector Store returned from extraction.")
    
    return {
        "transcript": transcript,
        "chunks": [split.page_content for split in splits],
        "total_chunks": len(splits),
        "vector_store_created": vector_store is not None
    }

@app.post("/search")
async def search_vector_store(request: SearchRequest):
    global GLOBAL_VECTOR_STORE
    if not GLOBAL_VECTOR_STORE:
        raise HTTPException(status_code=400, detail="Vector store not initialized. Please train the agent with a YouTube URL first.")
    
    print(f"🔍 Searching for: {request.query}")
    results = GLOBAL_VECTOR_STORE.similarity_search(request.query, k=request.k)
    
    return {
        "results": [
            {"content": doc.page_content, "metadata": doc.metadata} 
            for doc in results
        ]
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    global GLOBAL_VECTOR_STORE
    query = request.message
    print(f"💬 Received chat query: {query}")
    
    context = ""
    if GLOBAL_VECTOR_STORE:
        print("📚 Vector store found. Retrieving context...")
        results = GLOBAL_VECTOR_STORE.similarity_search(query, k=5)
        context = "\n\n".join([doc.page_content for doc in results])
        print(f"📄 Retrieved {len(results)} chunks of context.")
    else:
        print("⚠️ No vector store found. Answering without context.")
        return {"response": "Please provide a YouTube URL to train the agent first."}

    # Generate Response using LLM
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)
        
        template = """
        You are the professional AI persona of the speaker from the provided video transcript. 
        Your task is to answer viewer questions based STRICTLY on the content of the video context provided below.

        Instructions:
        1. **Persona:** Speak in the first person ("I", "we") as if you are the creator of the video. Be professional, engaging, and helpful.
        2. **Knowledge Limit:** You can only answer based on the "Context" section below. Do not use outside knowledge.
        3. **Failure Case:** If the answer to the question cannot be found in the context, do not make up an answer. Instead, strictly reply with this exact phrase: 
           "Seems like you are asking questions that I can't find any answer for from my training data."

        Context:
        {context}
        
        User Question:
        {question}
        
        Answer:
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm
        
        response = chain.invoke({"question": query, "context": context})
        print("🤖 Generated response.")
        
        return {"response": response.content}
        
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
