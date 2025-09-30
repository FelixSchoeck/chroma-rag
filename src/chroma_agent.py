from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from chroma_interaction_class import ChromaInteractionClass
import os
import asyncio
import uuid

# Global ChromaDB client reference
_chroma_client = None

def set_chroma_client(client: ChromaInteractionClass):
    """Set the global ChromaDB client."""
    global _chroma_client
    _chroma_client = client

def store_documents(documents: list[str]) -> dict:
    """Store documents in the ChromaDB collection.
    
    Args:
        documents: List of document strings to store in the database.
        
    Returns:
        dict: Status and message about the storage operation.
    """
    if _chroma_client is None:
        return {"status": "error", "error_message": "ChromaDB client not initialized."}
    
    try:
        _chroma_client.store_data(documents)
        return {"status": "success", "message": f"Successfully stored {len(documents)} documents in ChromaDB."}
    except Exception as e:
        return {"status": "error", "error_message": f"Error storing documents: {str(e)}"}

def query_documents(query: str, n_results: int = 5) -> dict:
    """Search and retrieve relevant documents from the ChromaDB collection.
    
    Args:
        query: Search query string to find relevant documents.
        n_results: Maximum number of documents to return (default: 5).
        
    Returns:
        dict: Status and documents or error message.
    """
    if _chroma_client is None:
        return {"status": "error", "error_message": "ChromaDB client not initialized."}
    
    try:
        results = _chroma_client.query_data(query, n_results=n_results)
        if results and 'documents' in results and results['documents'][0]:
            docs = results['documents'][0]
            return {
                "status": "success", 
                "documents": docs,
                "count": len(docs)
            }
        else:
            return {"status": "empty", "message": f"No documents found matching: '{query}'"}
    except Exception as e:
        return {"status": "error", "error_message": f"Error querying documents: {str(e)}"}

# Create FunctionTools
store_tool = FunctionTool(store_documents)
query_tool = FunctionTool(query_documents)

class ChromaAgentRunner:
    """Runner wrapper for ChromaDB Agent following Google ADK pattern."""
    
    def __init__(self, chroma_client: ChromaInteractionClass, model: str, instructions: str, api_key: str = None):
        # Validate chroma_client
        if chroma_client is None:
            raise ValueError("chroma_client cannot be None")
        
        # Set API key if provided
        if api_key:
            os.environ['GOOGLE_API_KEY'] = api_key
        
        # Set global chroma client for tools
        set_chroma_client(chroma_client)
        
        # Create Agent with tools (following the example)
        self.agent = Agent(
            model=model,
            name="chroma_db_assistant",
            instruction=f"""{instructions}

**If the user wants to store documents or information, use the 'store_documents' tool.**
**If the 'store_documents' tool returns a 'success' status, confirm to the user that the documents were stored.**
**If the 'store_documents' tool returns an 'error' status, inform the user about the error.**

**If the user asks questions or wants to retrieve information, use the 'query_documents' tool to search for relevant documents.**
**If the 'query_documents' tool returns a 'success' status, provide the found documents to the user.**
**If the 'query_documents' tool returns an 'empty' status, inform the user that no relevant documents were found.**
**If the 'query_documents' tool returns an 'error' status, inform the user about the error.**

You can use these tools as needed to help the user with document storage and retrieval.""",
            tools=[store_tool, query_tool]
        )
        
        # Session setup
        self.app_name = "chroma_rag_app"
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"
        self.session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        # Session service and runner
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=self.agent, 
            app_name=self.app_name, 
            session_service=self.session_service
        )
        
        # Initialize session
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize the session asynchronously."""
        async def init():
            await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=self.session_id
            )
        
        # Run in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # If loop is already running, we need to schedule it
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, init())
                future.result()
        else:
            loop.run_until_complete(init())
    
    def send_message(self, message: str) -> str:
        """Send a message to the agent and get response."""
        try:
            # Create content
            content = types.Content(role='user', parts=[types.Part(text=message)])
            
            # Run the agent
            events = self.runner.run(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=content
            )
            
            # Extract final response
            for event in events:
                if event.is_final_response():
                    return event.content.parts[0].text
            
            return "No response received from agent."
                
        except Exception as e:
            return f"Error processing message: {str(e)}"

def create_chroma_agent(chroma_client: ChromaInteractionClass, model: str, instructions: str, api_key: str = None):
    """Create a ChromaDB agent runner with the specified configuration."""
    return ChromaAgentRunner(chroma_client, model, instructions, api_key)
    
    