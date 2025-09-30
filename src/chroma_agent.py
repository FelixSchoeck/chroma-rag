from google.adk.agents import LlmAgent
from chroma_interaction_class import ChromaInteractionClass
import os

# Global ChromaDB client reference
_chroma_client = None

def set_chroma_client(client: ChromaInteractionClass):
    """Set the global ChromaDB client."""
    global _chroma_client
    _chroma_client = client

def store_documents(documents: list[str]) -> str:
    """Store documents in the ChromaDB collection."""
    if _chroma_client is None:
        return "Error: ChromaDB client not initialized."
    
    _chroma_client.store_data(documents)
    return f"Successfully stored {len(documents)} documents in ChromaDB."

def query_documents(query: str, n_results: int = 5) -> str:
    """Query documents from the ChromaDB collection."""
    if _chroma_client is None:
        return "Error: ChromaDB client not initialized."
    
    results = _chroma_client.query_data(query, n_results=n_results)
    if results and 'documents' in results and results['documents'][0]:
        docs = results['documents'][0]
        response = f"Found {len(docs)} relevant documents:\n\n"
        for i, doc in enumerate(docs, 1):
            response += f"Document {i}: {doc[:200]}...\n\n"
        return response
    else:
        return f"No documents found for query: '{query}'"

def create_chroma_agent(chroma_client: ChromaInteractionClass, model: str, instructions: str, api_key: str = None):
    """Create a ChromaDB agent with the specified configuration."""
    
    # Set API key if provided
    if api_key:
        os.environ['GOOGLE_API_KEY'] = api_key
    
    # Set global chroma client
    set_chroma_client(chroma_client)
    
    # Create agent with tools
    agent = LlmAgent(
        model=model,
        name="chroma_db_assistant",
        description="An AI assistant that can store and query documents using ChromaDB.",
        instruction=instructions,
        tools=[store_documents, query_documents]  # Pass functions directly
    )
    
    return agent
    
    