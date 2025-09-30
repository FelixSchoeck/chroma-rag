"""
ChromaDB Admin Interface - Streamlit App
Startet die Admin-Oberfläche für ChromaDB Interaktion.
"""

import sys
import os

# Füge das src-Verzeichnis zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.admin_view import AdminView

if __name__ == "__main__":
    admin_view = AdminView()
    admin_view.run()