import os
import shutil
import time
import random
import logging
from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader, PyPDFLoader
from langchain_community.docstore.document import Document
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# Load environment variables
load_dotenv()

# Configuration
DATA_DIR = "./data"
DB_DIR = "./chroma_db"

# Chunking for Gemini 3 Flash
CHUNK_SIZE = 2000  
CHUNK_OVERLAP = 200

# Embedding model
EMBEDDING_MODEL = "gemini-embedding-001"

def load_pdf_triple_fallback(file_path):
    """
    Attempts to load a PDF using 3 different libraries.
    1. PyMuPDF (Fastest, best metadata)
    2. PyPDF (Standard fallback)
    3. PDFPlumber (Slowest, but handles corrupt/weird PDFs best)
    """
    filename = os.path.basename(file_path)
    
    # --- STRATEGY 1: PyMuPDF ---
    try:
        loader = PyMuPDFLoader(file_path)
        docs = loader.load()
        if docs and any(d.page_content.strip() for d in docs):
            return docs
    except Exception:
        pass # Silently fail to next strategy

    print(f"  > PyMuPDF failed/empty for {filename}. Trying Strategy 2 (PyPDF)...")

    # --- STRATEGY 2: PyPDF ---
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        if docs and any(d.page_content.strip() for d in docs):
            return docs
    except Exception:
        pass

    print(f"  > PyPDF failed for {filename}. Trying Strategy 3 (PDFPlumber)...")

    # --- STRATEGY 3: PDFPlumber (Last Resort)---
    try:
        docs = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    # Manually create LangChain Document
                    docs.append(Document(
                        page_content=text,
                        metadata={"source": filename, "page": i + 1}
                    ))
        if docs:
            return docs
    except Exception as e:
        print(f"  ! PDFPlumber failed for {filename}: {e}")

    # If we get here, the file is likely an image scan or completely corrupt
    return None

def add_documents_with_backoff(vector_store, batch, retries=5):
    """
    Adds documents to Chroma with exponential backoff for 429 errors.
    """
    for attempt in range(retries):
        try:
            vector_store.add_documents(documents=batch)
            return True
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"    ! Rate limit hit. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                print(f"    ! Error adding batch: {e}")
                raise e
    return False

def ingest_documents():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created {DATA_DIR}. Please put your PDF files here.")
        return

    print(f"Initializing Embedding Model ({EMBEDDING_MODEL})...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=api_key,
        task_type="retrieval_document"
    )

    all_splits = []
    pdf_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.pdf')]

    if not pdf_files:
        print("No PDF files found in /data.")
        return

    print(f"Processing {len(pdf_files)} documents...")

    for filename in pdf_files:
        file_path = os.path.join(DATA_DIR, filename)
        
        # Check size (Skip 0 byte files)
        if os.path.getsize(file_path) == 0:
            print(f"  ! SKIPPING {filename}: File size is 0 bytes.")
            continue

        docs = load_pdf_triple_fallback(file_path)
        
        if not docs:
            print(f"  ! FAILED {filename}: All extraction methods failed. Skipping.")
            continue

        # Clean Metadata
        for doc in docs:
            doc.metadata["source"] = filename
            # Ensure page exists and is integer
            if "page" in doc.metadata:
                try:
                    doc.metadata["page"] = int(doc.metadata["page"])
                    if doc.metadata["page"] == 0: doc.metadata["page"] = 1
                except:
                    doc.metadata["page"] = 1
            else:
                doc.metadata["page"] = 1

        # Split Text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, 
            chunk_overlap=CHUNK_OVERLAP
        )
        splits = text_splitter.split_documents(docs)
        
        if splits:
            all_splits.extend(splits)
            print(f"  - Loaded {filename}: {len(splits)} chunks")
        else:
            print(f"  - Loaded {filename}: 0 chunks (Empty text layer?)")

    if not all_splits:
        print("No valid chunks created. Exiting.")
        return

    # Create/Reset Vector Store
    if os.path.exists(DB_DIR):
        try:
            shutil.rmtree(DB_DIR)
        except PermissionError:
            print("Error: Could not delete old DB. Close open apps and retry.")
            return
        
    print(f"Creating vector store with {len(all_splits)} chunks...")
    
    vector_store = Chroma(
        embedding_function=embeddings,
        persist_directory=DB_DIR
    )
    
    # BATCH PROCESSING
    batch_size = 25
    total_batches = (len(all_splits) // batch_size) + 1
    
    print(f"Starting ingestion in {total_batches} batches...")
    
    for i in range(0, len(all_splits), batch_size):
        batch = all_splits[i:i+batch_size]
        try:
            add_documents_with_backoff(vector_store, batch)
            print(f"  - Processed batch {i//batch_size + 1}/{total_batches}")
            time.sleep(1.5) 
        except Exception as e:
            print(f"Critical error on batch {i}: {e}")
            break
    
    print("Ingestion Complete! Vector store saved to ./chroma_db")

if __name__ == "__main__":
    ingest_documents()