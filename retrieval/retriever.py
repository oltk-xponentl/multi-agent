from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

# MUST MATCH INGEST.PY
EMBEDDING_MODEL = "gemini-embedding-001"
DB_DIR = "./chroma_db"

def retrieve_documents(query: str, k: int = 5) -> str:
    """
    Retrieves documents from ChromaDB.
    """
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "Error: GOOGLE_API_KEY not found."

        # Initialize Embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            google_api_key=api_key,
            task_type="retrieval_query"
        )
        
        # Connect to DB
        vector_store = Chroma(
            embedding_function=embeddings,
            persist_directory=DB_DIR
        )
        
        # Perform Search
        results = vector_store.similarity_search(query, k=k)
        
        formatted_results = []
        for doc in results:
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "Unknown")
            # Clean up newlines for cleaner injection into LLM prompt
            content = doc.page_content.replace("\n", " ")
            
            formatted_results.append(
                f"--- DOCUMENT SEGMENT ---\n"
                f"SOURCE: {source}, PAGE: {page}\n"
                f"CONTENT: {content}\n"
            )
            
        return "\n".join(formatted_results)
    except Exception as e:
        return f"Error retrieving documents: {e}"