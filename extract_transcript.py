from langchain_community.document_loaders import YoutubeLoader

def extract_transcript(video_url):
    print(f"Attempting to fetch transcript for: {video_url}")
    try:
        # Try to get transcript with English translation first
        loader = YoutubeLoader.from_youtube_url(
            video_url,
            add_video_info=False,
            language=["en", "en-US"],
            translation="en"
        )
        documents = loader.load()
    except Exception as e:
        print(f"Could not get English transcript/translation: {e}")
        print("Attempting to fetch any available transcript...")
        try:
            # Fallback: Try to get any transcript (no translation forced)
            loader = YoutubeLoader.from_youtube_url(
                video_url,
                add_video_info=False
            )
            documents = loader.load()
        except Exception as e2:
            return f"Error: Failed to fetch any transcript: {e2}"
    
    if not documents:
        return "Error: No transcript found."

    # Return the content
    full_transcript = "\n".join([doc.page_content for doc in documents])
    
    
    # Text Splitting
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True,
    )
    all_splits = text_splitter.split_documents(documents)
    
    # Embedding and Vector Store
    try:
        import os
        from dotenv import load_dotenv
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain_core.vectorstores import InMemoryVectorStore
        
        # Load environment variables from .env file
        load_dotenv()
        
        # Check for API Key
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print("⚠️ GOOGLE_API_KEY not found in environment or .env file.")
            print("   Skipping embedding and vector storage.")
            return full_transcript, all_splits, None

        print(f"🔑 Found GOOGLE_API_KEY: {api_key[:5]}...{api_key[-5:]}")
        print("🧠 Initializing Gemini Embeddings (models/text-embedding-004)...")
        
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        vector_store = InMemoryVectorStore(embeddings)
        
        print(f"📥 Indexing {len(all_splits)} chunks into Vector Store...")
        document_ids = vector_store.add_documents(documents=all_splits)
        print(f"✅ Indexed {len(document_ids)} chunks.")
        
        # Verify by printing a sample embedding (if possible) or performing a similarity search
        # Since we can't easily peek into InMemoryVectorStore's raw storage without private access,
        # we will perform a dummy similarity search to prove it works.
        print("🔍 Verifying Vector Store with a test query...")
        
        # Let's also print the raw embedding for the first chunk to show it's working
        first_chunk_text = all_splits[0].page_content
        print(f"🧬 Generating embedding for first chunk (first 50 chars): '{first_chunk_text[:50]}...'")
        raw_embedding = embeddings.embed_query(first_chunk_text)
        print(f"🔢 Raw Embedding Vector (first 5 dimensions): {raw_embedding[:5]}... (Total dimensions: {len(raw_embedding)})")

        results = vector_store.similarity_search("test", k=1)
        if results:
            print(f"✅ Verification successful! Found document: {results[0].page_content[:50]}...")
        
        return full_transcript, all_splits, vector_store
        
    except Exception as e:
        print(f"⚠️ Error during embedding/indexing: {e}")
        return full_transcript, all_splits, None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter YouTube Video URL: ")
    
    if url:
        result = extract_transcript(url)
        if isinstance(result, tuple) and len(result) == 3:
             transcript, splits, vector_store = result
             print(f"Total Chunks: {len(splits)}")
             if vector_store:
                 print("Vector Store: Initialized and populated.")
             else:
                 print("Vector Store: Not initialized.")
        elif isinstance(result, str):
             print(result)
    else:
        print("Please provide a valid URL.")
