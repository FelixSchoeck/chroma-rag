import streamlit as st
from chroma_interaction_class import ChromaInteractionClass
import json


class AdminView:
    """Streamlit-basierte Admin-Oberfläche für ChromaDB Interaktion."""
    
    def __init__(self):
        self.chroma_client = None
        
    def init_session_state(self):
        """Initialisiert den Streamlit Session State."""
        if 'connected' not in st.session_state:
            st.session_state.connected = False
        if 'chroma_client' not in st.session_state:
            st.session_state.chroma_client = None
        if 'documents_added' not in st.session_state:
            st.session_state.documents_added = 0
            
    def connection_sidebar(self):
        """Sidebar für Datenbankverbindung."""
        st.sidebar.header("🔗 HTTP Datenbankverbindung")
        
        # Verbindungsparameter
        st.sidebar.info("🌐 Verbindung zu ChromaDB HTTP Server")
        host = st.sidebar.text_input("Host", value="localhost")
        port = st.sidebar.number_input("Port", value=8000, min_value=1, max_value=65535)
        collection_name = st.sidebar.text_input("Collection Name", value="documents")
        client_name = st.sidebar.text_input("Client Name", value="admin_client")
        
        # Verbinden Button
        if st.sidebar.button("Verbinden"):
            try:
                self.chroma_client = ChromaInteractionClass(host, port, collection_name, client_name)
                self.chroma_client.connect()
                st.session_state.chroma_client = self.chroma_client
                st.session_state.connected = True
                st.sidebar.success("✅ Verbindung erfolgreich!")
            except Exception as e:
                st.sidebar.error(f"❌ Verbindungsfehler: {str(e)}")
                st.session_state.connected = False
        
        # Verbindungsstatus anzeigen
        if st.session_state.connected:
            st.sidebar.success("🟢 Verbunden")
        else:
            st.sidebar.warning("🔴 Nicht verbunden")
            
        # Trennen Button
        if st.session_state.connected and st.sidebar.button("Trennen"):
            st.session_state.connected = False
            st.session_state.chroma_client = None
            st.sidebar.info("Verbindung getrennt")
            
    def add_documents_section(self):
        """Sektion zum Hinzufügen von Dokumenten."""
        st.header("📄 Dokumente hinzufügen")
        
        if not st.session_state.connected:
            st.warning("⚠️ Bitte stellen Sie zuerst eine Verbindung zur Datenbank her.")
            return
            
        # Tab-Auswahl für verschiedene Input-Methoden
        tab1, tab2, tab3 = st.tabs(["Einzelnes Dokument", "Multiple Dokumente", "Datei Upload"])
        
        with tab1:
            st.subheader("Einzelnes Dokument hinzufügen")
            single_doc = st.text_area("Dokumentinhalt:", height=150)
            if st.button("Dokument hinzufügen", key="single_doc"):
                if single_doc.strip():
                    try:
                        print(single_doc)
                        st.session_state.chroma_client.store_data(single_doc)
                        st.success("✅ Dokument erfolgreich hinzugefügt!")
                        st.session_state.documents_added += 1
                    except Exception as e:
                        st.error(f"❌ Fehler beim Hinzufügen: {str(e)}")
                else:
                    st.warning("⚠️ Bitte geben Sie Dokumentinhalt ein.")
                    
        with tab2:
            st.subheader("Multiple Dokumente hinzufügen")
            multi_docs = st.text_area(
                "Dokumente (ein Dokument pro Zeile):", 
                height=200,
                help="Geben Sie jedes Dokument in einer neuen Zeile ein."
            )
            if st.button("Dokumente hinzufügen", key="multi_docs"):
                if multi_docs.strip():
                    docs_list = [doc.strip() for doc in multi_docs.split('\n') if doc.strip()]
                    if docs_list:
                        try:
                            st.session_state.chroma_client.store_data(docs_list)
                            st.success(f"✅ {len(docs_list)} Dokumente erfolgreich hinzugefügt!")
                            st.session_state.documents_added += len(docs_list)
                        except Exception as e:
                            st.error(f"❌ Fehler beim Hinzufügen: {str(e)}")
                    else:
                        st.warning("⚠️ Keine gültigen Dokumente gefunden.")
                else:
                    st.warning("⚠️ Bitte geben Sie Dokumentinhalte ein.")
                    
        with tab3:
            st.subheader("Dokumente aus Datei hochladen")
            uploaded_file = st.file_uploader(
                "Datei auswählen", 
                type=['txt', 'json'],
                help="Unterstützte Formate: TXT (ein Dokument pro Zeile), JSON (Array von Strings)"
            )
            if uploaded_file and st.button("Datei verarbeiten", key="file_upload"):
                try:
                    if uploaded_file.type == "text/plain":
                        content = str(uploaded_file.read(), "utf-8")
                        docs_list = [doc.strip() for doc in content.split('\n') if doc.strip()]
                    elif uploaded_file.type == "application/json":
                        content = json.load(uploaded_file)
                        if isinstance(content, list):
                            docs_list = [str(doc) for doc in content if str(doc).strip()]
                        else:
                            st.error("❌ JSON-Datei muss ein Array von Strings enthalten.")
                            return
                    else:
                        st.error("❌ Nicht unterstütztes Dateiformat.")
                        return
                        
                    if docs_list:
                        st.session_state.chroma_client.store_data(docs_list)
                        st.success(f"✅ {len(docs_list)} Dokumente aus Datei erfolgreich hinzugefügt!")
                        st.session_state.documents_added += len(docs_list)
                    else:
                        st.warning("⚠️ Keine gültigen Dokumente in der Datei gefunden.")
                        
                except Exception as e:
                    st.error(f"❌ Fehler beim Verarbeiten der Datei: {str(e)}")
                    
    def query_section(self):
        """Sektion zum Abfragen der Datenbank."""
        st.header("🔍 Datenbank abfragen")
        
        if not st.session_state.connected:
            st.warning("⚠️ Bitte stellen Sie zuerst eine Verbindung zur Datenbank her.")
            return
            
        # Query-Parameter
        col1, col2 = st.columns([3, 1])
        with col1:
            query_text = st.text_input("Suchanfrage:", placeholder="Geben Sie Ihre Suchanfrage ein...")
        with col2:
            n_results = st.number_input("Anzahl Ergebnisse", min_value=1, max_value=100, value=5)
            
        if st.button("Suchen", key="search"):
            if query_text.strip():
                try:
                    results = st.session_state.chroma_client.query_data(query_text, n_results)
                    
                    if results and 'documents' in results and results['documents'][0]:
                        st.subheader("📋 Suchergebnisse:")
                        for i, doc in enumerate(results['documents'][0], 1):
                            with st.expander(f"Ergebnis {i}"):
                                st.write(doc)
                                if 'distances' in results and results['distances'][0]:
                                    st.caption(f"Distanz: {results['distances'][0][i-1]:.4f}")
                    else:
                        st.info("📭 Keine Ergebnisse gefunden.")
                        
                except Exception as e:
                    st.error(f"❌ Fehler bei der Suche: {str(e)}")
            else:
                st.warning("⚠️ Bitte geben Sie eine Suchanfrage ein.")
                
    def database_overview_section(self):
        """Sektion für Datenbankübersicht."""
        st.header("📊 Datenbankübersicht")
        
        if not st.session_state.connected:
            st.warning("⚠️ Bitte stellen Sie zuerst eine Verbindung zur Datenbank her.")
            return
            
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Dokumente hinzugefügt (Session)", st.session_state.documents_added)
            
        with col2:
            if st.button("Alle Daten anzeigen", key="show_all"):
                try:
                    all_data = st.session_state.chroma_client.show_all_data()
                    if all_data and 'documents' in all_data and all_data['documents']:
                        st.metric("Gesamt Dokumente", len(all_data['documents']))
                        
                        # Alle Dokumente anzeigen
                        st.subheader("📄 Alle Dokumente:")
                        for i, doc in enumerate(all_data['documents'], 1):
                            with st.expander(f"Dokument {i} (ID: {all_data['ids'][i-1] if 'ids' in all_data else 'N/A'})"):
                                st.write(doc)
                    else:
                        st.metric("Gesamt Dokumente", 0)
                        st.info("📭 Keine Dokumente in der Datenbank.")
                        
                except Exception as e:
                    st.error(f"❌ Fehler beim Laden der Daten: {str(e)}")
                    
        with col3:
            st.button("🔄 Aktualisieren", key="refresh")
            
    def run(self):
        """Hauptmethode zum Ausführen der Admin-Oberfläche."""
        st.set_page_config(
            page_title="ChromaDB Admin",
            page_icon="🗄️",
            layout="wide"
        )
        
        st.title("🗄️ ChromaDB Admin Interface")
        st.markdown("---")
        
        # Session State initialisieren
        self.init_session_state()
        
        # Sidebar für Verbindung
        self.connection_sidebar()
        
        # Hauptbereich
        if st.session_state.connected:
            self.chroma_client = st.session_state.chroma_client
            
        # Hauptsektionen
        self.add_documents_section()
        st.markdown("---")
        self.query_section()
        st.markdown("---")
        self.database_overview_section()


if __name__ == "__main__":
    admin_view = AdminView()
    admin_view.run()