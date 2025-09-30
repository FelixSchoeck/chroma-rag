"""
ChromaDB Interface - Streamlit App
Multi-page app with Admin and Chat interfaces.
"""

import sys
import os
import streamlit as st

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.admin_view import AdminView
from src.llm_chat import ChatView

def main():
    st.set_page_config(
        page_title="ChromaDB Interface",
        page_icon="🗄️",
        layout="wide"
    )
    
    # Sidebar navigation
    st.sidebar.title("🗄️ ChromaDB Interface")
    page = st.sidebar.selectbox(
        "Choose Interface:",
        ["💬 AI Chat Assistant", "🛠️ Admin Panel"]
    )
    
    if page == "💬 AI Chat Assistant":
        chat_view = ChatView()
        chat_view.run()
    elif page == "🛠️ Admin Panel":
        admin_view = AdminView()
        admin_view.run()

if __name__ == "__main__":
    main()