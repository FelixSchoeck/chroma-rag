import streamlit as st
import json
from datetime import datetime
from chroma_interaction_class import ChromaInteractionClass


class ChatView:
    """Streamlit-based chat interface for ChromaDB agent."""
    
    def __init__(self):
        self.chroma_client = None
        self.agent = None
        
    def init_session_state(self):
        """Initialize Streamlit session state."""
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        if 'chroma_connected' not in st.session_state:
            st.session_state.chroma_connected = False
        if 'chroma_client' not in st.session_state:
            st.session_state.chroma_client = None
        if 'agent' not in st.session_state:
            st.session_state.agent = None
            
        # Auto-initialize ChromaDB connection if not already done
        if not st.session_state.chroma_connected and st.session_state.chroma_client is None:
            self.auto_connect_chroma()
            
    def auto_connect_chroma(self):
        """Automatically connect to ChromaDB with default settings."""
        try:
            # Fixed connection settings
            host = "localhost"
            port = 8000
            collection_name = "documents"
            client_name = "chat_client"
            
            # Create ChromaDB client
            self.chroma_client = ChromaInteractionClass(host, port, collection_name, client_name)
            self.chroma_client.connect()
            
            # Store in session state
            st.session_state.chroma_client = self.chroma_client
            st.session_state.chroma_connected = True
            
        except Exception as e:
            st.session_state.chroma_connected = False
            st.error(f"❌ Automatische ChromaDB-Verbindung fehlgeschlagen: {str(e)}")
            st.error("Stellen Sie sicher, dass ChromaDB Server auf localhost:8000 läuft.")

    def agent_setup(self):
        """Setup AI agent in sidebar."""
        st.sidebar.header("🤖 AI Agent Setup")
        
        # Connection status
        if st.session_state.chroma_connected:
            st.sidebar.success("🟢 ChromaDB Connected (localhost:8000)")
            st.sidebar.info("📁 Collection: documents")
        else:
            st.sidebar.error("🔴 ChromaDB Connection Failed")
            st.sidebar.warning("Stelle sicher, dass ChromaDB Server läuft")
            return
        
        # API Configuration
        st.sidebar.subheader("🔑 API Configuration")
        api_key = st.sidebar.text_input(
            "Google AI API Key", 
            type="password",
            placeholder="Geben Sie Ihren Google AI API Key ein...",
            help="Benötigt für die Nutzung der Gemini-Modelle",
            key="api_key"
        )
        
        if not api_key:
            st.sidebar.warning("⚠️ API Key erforderlich")
            st.sidebar.info("Holen Sie sich einen kostenlosen API Key: https://makersuite.google.com/app/apikey")
            return
        
        # Agent Configuration
        st.sidebar.subheader("🎯 Agent Configuration")
        model_options = {
            "gemini-2.5-flash": "Gemini 2.5 Flash - Schnellstes Modell",
            "gemini-2.5-pro": "Gemini 2.5 Pro - Bestes Reasoning"
        }
        
        selected_model = st.sidebar.selectbox(
            "Model", 
            list(model_options.keys()),
            format_func=lambda x: model_options[x],
            index=0,
            key="chat_model",
            help="Wählen Sie das gewünschte Gemini-Modell"
        )
        model_name = selected_model
        
        system_prompt = st.sidebar.text_area(
            "System Prompt",
            value="You are a helpful AI assistant with access to a ChromaDB knowledge base. Use the available tools to store and query documents to help users with their questions.",
            height=100,
            key="chat_system_prompt"
        )
        
        # Initialize agent button
        if st.sidebar.button("🚀 Initialize Agent", key="init_agent"):
            try:
                # Import the agent creation function
                from chroma_agent import create_chroma_agent
                
                # Create agent with the correct Google ADK pattern
                self.agent = create_chroma_agent(
                    chroma_client=self.chroma_client,
                    model=model_name,
                    instructions=system_prompt,
                    api_key=api_key
                )
                
                # Store in session state
                st.session_state.agent = self.agent
                
                st.sidebar.success("✅ Agent initialized successfully!")
                
                # Add welcome message
                welcome_msg = {
                    "role": "assistant",
                    "content": "🤖 Hello! I'm your ChromaDB assistant. I can help you store and query documents from your knowledge base. I'm connected to localhost:8000/documents and ready to help!",
                    "timestamp": datetime.now()
                }
                if not any(msg.get("content") == welcome_msg["content"] for msg in st.session_state.chat_messages):
                    st.session_state.chat_messages.append(welcome_msg)
                
            except Exception as e:
                st.sidebar.error(f"❌ Error initializing agent: {str(e)}")
        
        # Agent status
        if st.session_state.agent:
            st.sidebar.success("🤖 Agent Ready")
            if st.sidebar.button("🔄 Reset Agent", key="reset_agent"):
                st.session_state.agent = None
                st.sidebar.info("Agent reset")
        else:
            st.sidebar.warning("🤖 Agent Not Initialized")
            
        # Tools Information
        st.sidebar.subheader("🛠️ Available Tools")
        st.sidebar.info(
            """
            **Agent Tools:**
            - 📄 `store_documents`: Store new documents
            - 🔍 `query_documents`: Search existing documents
            
            **Usage Examples:**
            - "Store these documents: [doc1, doc2]"
            - "Search for information about AI"
            - "Add this document to the database"
            """
        )
        
    def chat_interface(self):
        """Main chat interface."""
        st.header("💬 ChromaDB AI Assistant")
        
        if not st.session_state.chroma_connected:
            st.error("❌ ChromaDB-Verbindung fehlgeschlagen")
            st.info("Stellen Sie sicher, dass ChromaDB Server auf localhost:8000 läuft und starten Sie die App neu.")
            st.code("chroma run --host localhost --port 8000")
            return
            
        if not st.session_state.agent:
            st.warning("⚠️ Bitte initialisieren Sie den AI-Agent in der Sidebar.")
            st.info("👈 Verwenden Sie die Sidebar um den Agent zu konfigurieren.")
            return
            
        # Get current agent from session state
        if st.session_state.agent:
            self.agent = st.session_state.agent
            self.chroma_client = st.session_state.chroma_client
        
        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
                    if "timestamp" in message:
                        st.caption(f"⏰ {message['timestamp'].strftime('%H:%M:%S')}")
        
        # Chat input
        if prompt := st.chat_input("Ask me anything about your documents..."):
            # Add user message
            user_msg = {
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now()
            }
            st.session_state.chat_messages.append(user_msg)
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
                st.caption(f"⏰ {user_msg['timestamp'].strftime('%H:%M:%S')}")
            
            # Generate agent response
            with st.chat_message("assistant"):
                with st.spinner("🤖 Thinking..."):
                    try:
                        # Use the correct LlmAgent method to generate response
                        response = self.agent.send_message(prompt)
                        
                        # Extract text from response
                        response_text = response.text if hasattr(response, 'text') else str(response)
                        
                        # Display response
                        st.write(response_text)
                        
                        # Add assistant message
                        assistant_msg = {
                            "role": "assistant", 
                            "content": response_text,
                            "timestamp": datetime.now()
                        }
                        st.session_state.chat_messages.append(assistant_msg)
                        st.caption(f"⏰ {assistant_msg['timestamp'].strftime('%H:%M:%S')}")
                        
                    except Exception as e:
                        error_msg = f"❌ Error: {str(e)}"
                        st.error(error_msg)
                        
                        # Add error message
                        error_assistant_msg = {
                            "role": "assistant",
                            "content": error_msg,
                            "timestamp": datetime.now()
                        }
                        st.session_state.chat_messages.append(error_assistant_msg)
                        
    def quick_actions(self):
        """Quick action buttons for common tasks."""
        if not st.session_state.chroma_connected or not st.session_state.agent:
            return
            
        st.subheader("⚡ Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📄 View All Documents", key="view_all"):
                try:
                    all_data = self.chroma_client.show_all_data()
                    if all_data and 'documents' in all_data:
                        count = len(all_data['documents'])
                        quick_msg = {
                            "role": "assistant",
                            "content": f"📊 Database contains {count} documents.\n\n" + 
                                     "\n".join([f"**Doc {i+1}:** {doc[:100]}..." 
                                              for i, doc in enumerate(all_data['documents'][:5])]),
                            "timestamp": datetime.now()
                        }
                        st.session_state.chat_messages.append(quick_msg)
                        st.rerun()
                    else:
                        st.info("No documents found in database.")
                except Exception as e:
                    st.error(f"Error retrieving documents: {e}")
        
        with col2:
            if st.button("🔍 Search Documents", key="quick_search"):
                search_query = st.text_input("Enter search query:", key="quick_search_input")
                if search_query:
                    quick_msg = {
                        "role": "user",
                        "content": f"Search for: {search_query}",
                        "timestamp": datetime.now()
                    }
                    st.session_state.chat_messages.append(quick_msg)
                    st.rerun()
        
        with col3:
            if st.button("📝 Add Document", key="quick_add"):
                doc_content = st.text_area("Enter document content:", key="quick_add_input")
                if doc_content:
                    quick_msg = {
                        "role": "user", 
                        "content": f"Store this document: {doc_content}",
                        "timestamp": datetime.now()
                    }
                    st.session_state.chat_messages.append(quick_msg)
                    st.rerun()
        
        with col4:
            if st.button("🗑️ Clear Chat", key="clear_chat"):
                st.session_state.chat_messages = []
                st.rerun()
                
    def export_chat(self):
        """Export chat history."""
        if st.session_state.chat_messages:
            st.subheader("💾 Export Chat")
            
            # Prepare export data
            export_data = {
                "chat_history": [
                    {
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": msg["timestamp"].isoformat() if "timestamp" in msg else None
                    }
                    for msg in st.session_state.chat_messages
                ],
                "exported_at": datetime.now().isoformat()
            }
            
            # Download button
            st.download_button(
                label="📥 Download Chat History",
                data=json.dumps(export_data, indent=2),
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
    def run(self):
        """Main method to run the chat interface."""
        st.set_page_config(
            page_title="ChromaDB Chat Assistant",
            page_icon="💬",
            layout="wide"
        )
        
        st.title("💬 ChromaDB AI Assistant")
        st.markdown("---")
        
        # Initialize session state
        self.init_session_state()
        
        # Setup sidebar
        self.agent_setup()
        
        # Main chat interface
        self.chat_interface()
        
        # Quick actions
        st.markdown("---")
        self.quick_actions()
        
        # Export functionality
        if st.session_state.chat_messages:
            st.markdown("---")
            self.export_chat()


if __name__ == "__main__":
    chat_view = ChatView()
    chat_view.run()