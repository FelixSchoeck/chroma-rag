import chromadb
from functools import wraps
import uuid

def require_connection(func):
    """
    Decorator that ensures the client is connected to a collection before executing the method.
    Raises ConnectionError if no connection is established.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, 'connection') or self.connection is None:
            raise ConnectionError(f"Not connected to collection '{self.collection_name}'. Please call connect() first.")
        return func(self, *args, **kwargs)
    return wrapper

class ChromaInteractionClass:
    """Class to interact with ChromaDB via HTTP."""
    
    def __init__(self, host, port, collection_name, name):
        self.name = name
        self.host = host
        self.port = port
        self.collection_name = collection_name
        
        # HTTP Client für Remote ChromaDB Server
        self.client = chromadb.HttpClient(host=host, port=port)
        self.connection = None
        
    def connect(self):
        """Establish connection to the ChromaDB collection."""
        self.connection = self.client.get_or_create_collection(name=self.collection_name)
        
    @require_connection
    def store_data(self, documents):
        """
        Store documents in the connected collection.
        
        Args: documents: List of strings (document content)
        """
        if isinstance(documents, str):
            documents = [documents]  # Convert single document to list
        
        # ChromaDB add() method expects specific parameters
        self.connection.add(
            documents=documents,
            ids=[str(uuid.uuid4()) for _ in documents]
        )
        
    @require_connection
    def query_data(self, query_texts, n_results=10):
        """Query data from the connected collection.
        
        Args:
            query_texts: List of query strings or single query string
            n_results: Number of results to return (default: 10)
        """
        if isinstance(query_texts, str):
            query_texts = [query_texts]
            
        return self.connection.query(
            query_texts=query_texts,
            n_results=n_results
        )

    @require_connection
    def show_all_data(self):
        """Show all data in the connected collection."""
        return self.connection.get()