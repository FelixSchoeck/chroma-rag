"""
ChromaDB Chat Assistant - Streamlit App
Starts the AI chat interface for ChromaDB interaction.
"""

import sys
import os

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.llm_chat import ChatView

if __name__ == "__main__":
    chat_view = ChatView()
    chat_view.run()