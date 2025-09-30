from google.adk.agents import Agent
from google.genai import types
from chroma_interaction_class import ChromaInteractionClass
from typing import Any
import os
import asyncio

class ChromaAgent(Agent):
    """Custom ChromaDB Agent following Google ADK pattern."""
    
    # Define fields that are allowed in Pydantic model
    chroma_client: Any = None
    model_name: str = ""
    system_instructions: str = ""
    
    def __init__(self, chroma_client: ChromaInteractionClass, model: str, instructions: str, api_key: str = None, **kwargs):
        # Set API key if provided
        if api_key:
            os.environ['GOOGLE_API_KEY'] = api_key
        
        # Initialize parent first with required fields
        super().__init__(name="chroma_db_assistant", **kwargs)
        
        # Set fields after initialization
        self.chroma_client = chroma_client
        self.model_name = model
        self.system_instructions = instructions
    
    async def run(self, request: types.Content, **kwargs) -> types.Content:
        """Main run method for processing user requests."""
        try:
            # Check if chroma_client is properly initialized
            if self.chroma_client is None:
                return types.Content(
                    parts=[types.Part(text="Error: ChromaDB client is not initialized.")]
                )
            
            # Get the user's message
            user_query = request.parts[0].text if request.parts else str(request)
            
            # Check if user wants to store documents
            if self._is_store_request(user_query):
                documents = self._extract_documents(user_query)
                if documents:
                    self.chroma_client.store_data(documents)
                    response_text = f"Successfully stored {len(documents)} documents in ChromaDB."
                else:
                    response_text = "No documents found to store."
            
            # Check if user wants to query documents  
            elif self._is_query_request(user_query):
                query = self._extract_query(user_query)
                results = self.chroma_client.query_data(query, n_results=5)
                if results and 'documents' in results and results['documents'][0]:
                    docs = results['documents'][0]
                    response_text = f"Found {len(docs)} relevant documents:\n\n"
                    for i, doc in enumerate(docs, 1):
                        response_text += f"Document {i}: {doc[:200]}...\n\n"
                else:
                    response_text = f"No documents found for query: '{query}'"
            
            # General LLM response with context
            else:
                # Try to find relevant context from ChromaDB
                try:
                    search_results = self.chroma_client.query_data(user_query, n_results=3)
                    context = ""
                    if search_results and 'documents' in search_results and search_results['documents'][0]:
                        context = "\n".join(search_results['documents'][0])
                except Exception as e:
                    context = ""
                    # If ChromaDB query fails, continue with simple LLM response
                
                # Create enhanced prompt
                prompt = f"{self.system_instructions}\n\n"
                if context:
                    prompt += f"Context from knowledge base: {context}\n\n"
                prompt += f"User query: {user_query}"
                
                # Use LLM to generate response
                try:
                    response = await self.llm.generate_content_async(prompt)
                    response_text = response.text if hasattr(response, 'text') else str(response)
                except Exception as llm_error:
                    # Fallback if LLM fails
                    response_text = f"I received your message: '{user_query}'. I'm a ChromaDB assistant ready to help with document storage and retrieval."
            
            # Return as Content
            return types.Content(
                parts=[types.Part(text=response_text)]
            )
            
        except Exception as e:
            error_text = f"Error processing request: {str(e)}"
            return types.Content(
                parts=[types.Part(text=error_text)]
            )
    
    def _is_store_request(self, query: str) -> bool:
        """Check if the query is requesting to store documents."""
        store_keywords = ['store', 'add', 'save', 'hinzufügen', 'speichern']
        return any(keyword in query.lower() for keyword in store_keywords)
    
    def _is_query_request(self, query: str) -> bool:
        """Check if the query is requesting to search documents."""
        query_keywords = ['search', 'find', 'query', 'suche', 'finde']
        return any(keyword in query.lower() for keyword in query_keywords)
    
    def _extract_documents(self, query: str) -> list[str]:
        """Extract documents to store from the query."""
        # Simple extraction - look for quoted strings or lists
        import re
        
        # Try to find quoted strings
        quoted_docs = re.findall(r'"([^"]*)"', query)
        if quoted_docs:
            return quoted_docs
        
        # Try to find list-like structures
        if '[' in query and ']' in query:
            try:
                import ast
                # Extract list from query
                start = query.find('[')
                end = query.rfind(']') + 1
                list_str = query[start:end]
                docs_list = ast.literal_eval(list_str)
                return [str(doc) for doc in docs_list if doc]
            except:
                pass
        
        # Fallback: treat everything after "store" as document
        if ':' in query:
            return [query.split(':', 1)[1].strip()]
        
        return []
    
    def _extract_query(self, query: str) -> str:
        """Extract the search query from the user input."""
        # Remove search keywords and return the rest
        query_keywords = ['search for', 'find', 'query', 'suche nach', 'finde']
        lower_query = query.lower()
        
        for keyword in query_keywords:
            if keyword in lower_query:
                return query[lower_query.find(keyword) + len(keyword):].strip()
        
        return query

class ChromaAgentRunner:
    """Runner wrapper for ChromaAgent."""
    
    def __init__(self, chroma_client: ChromaInteractionClass, model: str, instructions: str, api_key: str = None):
        # Validate chroma_client
        if chroma_client is None:
            raise ValueError("chroma_client cannot be None")
        
        self.agent = ChromaAgent(
            chroma_client=chroma_client,
            model=model, 
            instructions=instructions,
            api_key=api_key
        )
    
    def send_message(self, message: str) -> str:
        """Send a message to the agent and get response."""
        try:
            # Create request content
            request = types.Content(
                parts=[types.Part(text=message)]
            )
            
            # Run agent asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.agent.run(request))
            finally:
                loop.close()
            
            # Extract response text
            if hasattr(result, 'parts') and result.parts:
                return result.parts[0].text
            else:
                return str(result)
                
        except Exception as e:
            return f"Error processing message: {str(e)}"

def create_chroma_agent(chroma_client: ChromaInteractionClass, model: str, instructions: str, api_key: str = None):
    """Create a ChromaDB agent runner with the specified configuration."""
    return ChromaAgentRunner(chroma_client, model, instructions, api_key)
    
    