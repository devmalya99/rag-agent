from langchain_community.document_loaders import YoutubeLoader
import json

# -------------------------------------------------------------------------
# Transcript Extraction Generator
# Purpose: This function handles the pipeline of getting data from YouTube -> to Vector Store.
# Design Config:
#   - It is a Python GENERATOR (uses `yield`). This allows us to emit status updates 
#     (JSON strings) to the server step-by-step, enabling real-time UI feedback.
#   - Returns: A sequence of JSON status strings, ending with the populated Vector Store object.
# -------------------------------------------------------------------------
def extract_transcript_generator(video_url):
    # Step 1: Emit initial status
    yield json.dumps({"status": "fetching_transcript", "message": "Fetching transcript from YouTube..."}) + "\n"
    print(f"Attempting to fetch transcript for: {video_url}")
    
    # -------------------------------------------------------------------------
    # STICT Duration Check (Limit: 5 min)
    # Tool: yt-dlp (Robust & Reliable)
    # -------------------------------------------------------------------------
    try:
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True, # We only want metadata
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("⏳ Validating video duration...")
            info = ydl.extract_info(video_url, download=False)
            duration = info.get('duration', 0)
            
            if duration > 300: # 300 seconds = 5 minutes
                 yield json.dumps({
                    "status": "error", 
                    "message": f"❌ Video is too long ({int(duration/60)}m {int(duration%60)}s). Limit is 5 minutes."
                }) + "\n"
                 return
            
            print(f"✅ Duration check passed: {duration}s")
            
    except Exception as e:
        print(f"⚠️ Duration check failed: {e}")
        # STRICT MODE: If we can't verify duration, we REJECT.
        yield json.dumps({
            "status": "error", 
            "message": f"❌ Could not verify video duration. Processing stopped. Error: {str(e)}"
        }) + "\n"
        return

    # -------------------------------------------------------------------------
    # Transcript Extraction Layer
    # Logic: 
    #   1. Fetch transcript (Metadata check already done above).
    # -------------------------------------------------------------------------
    documents = None
    try:
        # Priority: English
        loader = YoutubeLoader.from_youtube_url(
            video_url,
            add_video_info=False, # We use yt-dlp for metadata now
            language=["en", "en-US"],
            translation="en"
        )
        documents = loader.load()
        
    except Exception as e:
        print(f"⚠️ English transcript failed: {e}")
        yield json.dumps({"status": "retry_transcript", "message": "English transcript not found. Trying auto-generated..."}) + "\n"
        
        try:
            loader = YoutubeLoader.from_youtube_url(
                video_url,
                add_video_info=False,
                language=["en", "en-US"]
            )
            documents = loader.load()
        except Exception as e2:
            yield json.dumps({"status": "error", "message": f"Failed to fetch transcript: {str(e2)}"}) + "\n"
            return

    if not documents:
        yield json.dumps({"status": "error", "message": "No transcript found."}) + "\n"
        return

    # Helper for UI status display
    full_transcript = "\n".join([doc.page_content for doc in documents])
    yield json.dumps({"status": "processing_text", "message": f"Transcript extracted ({len(full_transcript)} chars). Splitting text..."}) + "\n"
    
    # -------------------------------------------------------------------------
    # Text Splitting (Chunking)
    # Why: LLMs have token limits. We cannot feed an hour-long transcript at once.
    # Approach: RecursiveCharacterTextSplitter maintains context better than simple splitting 
    #           by keeping paragraphs/sentences together where possible.
    # Config: 1000 chars per chunk, 200 char overlap (to preserve context across boundaries).
    # -------------------------------------------------------------------------
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True,
    )
    all_splits = text_splitter.split_documents(documents)
    
    yield json.dumps({"status": "embedding", "message": f"Split into {len(all_splits)} chunks. Generating embeddings..."}) + "\n"
    
    # -------------------------------------------------------------------------
    # Embedding & Indexing
    # Logic: Convert text chunks -> Vector Embeddings -> Store in Memory.
    # -------------------------------------------------------------------------
    try:
        import os
        from dotenv import load_dotenv
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain_core.vectorstores import InMemoryVectorStore
        
        load_dotenv()
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            yield json.dumps({"status": "error", "message": "GOOGLE_API_KEY not found."}) + "\n"
            return

        print("🧠 Initializing Gemini Embeddings (models/text-embedding-004)...")
        
        # Model: text-embedding-004 is optimized for retrieval tasks.
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        vector_store = InMemoryVectorStore(embeddings)
        
        yield json.dumps({"status": "indexing", "message": "Indexing chunks into Vector Store..."}) + "\n"
        print(f"📥 Indexing {len(all_splits)} chunks into Vector Store...")
        
        document_ids = vector_store.add_documents(documents=all_splits)
        print(f"✅ Indexed {len(document_ids)} chunks.")
        
        yield json.dumps({
            "status": "complete", 
            "message": "Training complete! Agent is ready to chat.",
            "data": {
                "transcript_length": len(full_transcript),
                "total_chunks": len(all_splits),
                "vector_store_active": True
            }
        }) + "\n"
        
        # CRITICAL: Yield the vector store object itself so the server can access it.
        # This is the "return value" of our generator pipeline.
        yield vector_store 
        
    except Exception as e:
        print(f"⚠️ Error during embedding/indexing: {e}")
        yield json.dumps({"status": "error", "message": f"Embedding processing failed: {str(e)}"}) + "\n"

if __name__ == "__main__":
    import sys
    # Local Testing Block
    url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    print("Testing generator...")
    gen = extract_transcript_generator(url)
    for item in gen:
        if isinstance(item, str):
            print(item.strip())
        else:
            print("Received Vector Store object")

