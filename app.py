# Το Streamlit Web Interface για το UI :
# Το Streamlit είναι το νούμερο 1 εργαλείο για AI Engineers γιατί σου επιτρέπει να στήσεις ένα πλήρες chat interface με μόλις λίγες γραμμές Python.

import tempfile
from pathlib import Path
import streamlit as st                                              # δεν χρειαζόμαστε ούτε html/css
from langchain_core.messages import AIMessage, HumanMessage
from src.agent import EnterpriseAgentManager
from src.ingestion import DocumentIngestionPipeline
from src.vectorstore import SupabaseVectorStoreManager

# --- Ρυθμίσεις Σελίδας Streamlit ---
# ορίζει το εικονίδιο που θα φαίνεται στην καρτέλα του browser και τον τίτλο
st.set_page_config(
    page_title="Enterprise Multimodal RAG Assistant",
    page_icon="🤖", 
    layout="centered"
)

# Δημιουργούν τον τίτλο επικεφαλίδας και μια ωραία περιγραφή καλωσορίσματος στην κορυφή της σελίδας.
st.title("🤖 Enterprise-Grade Multimodal RAG & Agentic Assistant")
st.markdown("Ask me anything regarding your files! ")


# --- Sidebar: Διαχείριση & Drag-and-Drop Αρχείων (Secure Ephemeral Uploads) ---
st.sidebar.header("📁 Document Management")
st.sidebar.markdown(
    "Drag and Drop your files here. Everything is being processed with safety"
    " and is immediately deleted from the server after your session ends"
)


uploaded_files = st.sidebar.file_uploader(
    "Drag & Drop αρχείων",
    accept_multiple_files=True,
    type = ["pdf", "xlsx", "xls", "pptx", "md", "txt"],
)

if uploaded_files:
  # Αρχικοποίηση στο session state για να αποφύγουμε την επandεπεξεργασία σε κάθε chat reload
  if "processed_files_sig" not in st.session_state:
    st.session_state.processed_files_sig = None

  # Δημιουργία υπογραφής των τρεχόντων αρχείων (όνομα και μέγεθος)
  current_sig = tuple((f.name, f.size) for f in uploaded_files)

  # Ανεβάζει και επεξεργάζεται τα αρχεία αυτόματα μόνο αν είναι νέα/διαφορετικά
  if st.session_state.processed_files_sig != current_sig:
    # Δημιουργία ενός προσωρινού φακέλου ασφαλείας στη μνήμη/σύστημα
    with tempfile.TemporaryDirectory() as tmp_dir:
      with st.spinner("Μεταφόρτωση και εκτέλεση Ingestion Pipeline..."):
        try:
          # 1. Αποθηκεύουμε τα UploadedFiles προσωρινά μέσα στον προσωρινό φάκελο
          for uploaded_file in uploaded_files:
            temp_file_path = Path(tmp_dir) / uploaded_file.name
            with open(temp_file_path, "wb") as f:
              f.write(uploaded_file.getbuffer())  

          # 2. Καλούμε το Ingestion Pipeline δίνοντας του τον προσωρινό φάκελο!
          pipeline = DocumentIngestionPipeline(data_dir=tmp_dir)
          raw_elements = pipeline.process_all_files()

          # 3. Ανέβασμα των embeddings στη Supabase
          vector_manager = SupabaseVectorStoreManager()
          vector_manager.create_vectorstore(raw_elements)

          st.sidebar.success(
              "The RAG pipeline has beed completed!"
              "All of your files have been removed from the server automatically"
          )
          # Αποθήκευση της υπογραφής ώστε να μην ξανατρέξει άσκοπα
          st.session_state.processed_files_sig = current_sig

        except Exception as e:
          st.sidebar.error(f"Σφάλμα κατά την επεξεργασία των αρχείων: {e}")

      # (Μόλις τελειώσει αυτό το 'with' block, ο tmp_dir και τα περιεχόμενα
      #  του καταστρέφονται ολοκληρωτικά από τον server αυτόματα!)



# --- Αρχικοποίηση του Agent (Caching για να μην φορτώνει κάθε φορά).Χωρις την cache, καθε φορα που ο χρηστης θα παταγε enter για να στειλει το μνμ του θα εκανε reload ολο και θα ξαναεφτιαχνε τη συνδεση
#          απο την αρχη. Ετσι θα σπαταλουσε πορους και χρονο  ---
@st.cache_resource
def load_agent():
    manager = EnterpriseAgentManager()                                      # instance του EnterpriseAgentManager()
    return manager.get_agent_executor()

try:
    agent_executor = load_agent()                                           # δοκιμασε να τρεξεις την συναρτηση load_agent()
except Exception as e:
    st.error(f"Σφάλμα κατά την αρχικοποίηση: {e}")
    raise                                                                   # Διακόπτει αμέσως την εκτέλεση της εφαρμογής, ώστε να μην προσπαθήσει να συνεχίσει χωρίς να έχει αρχικοποιηθεί ο Agent.



# --- Διαχείριση Ιστορικού Συνομιλίας στο Session State ---
if "chat_history" not in st.session_state:                                  # Το st.session_state είναι ο ειδικός χώρος αποθήκευσης του Streamlit που θυμάται δεδομένα ανάμεσα στις ανανεώσεις της σελίδας
    st.session_state.chat_history = []                                      # αν δεν υπαρχει ηδη δημιουργουμε μια κενη λιστα 

# Εμφάνιση παλιών μηνυμάτων στην οθόνη
for message in st.session_state.chat_history:                               # Κάθε φορά που η σελίδα ξαναφορτώνεται, διατρέχουμε (loop) όλα τα προηγούμενα μηνύματα που έχουν αποθηκευτεί.
    if isinstance(message, HumanMessage):                                   # αν το μηνυμα ειναι του χρηστη
        with st.chat_message("user"):                                       # Δημιουργεί ένα οπτικό πλαίσιο συνομιλίας για τον χρήστη (με το αντίστοιχο εικονίδιο).
            st.markdown(message.content)                                    # Εκτυπώνει το κείμενο του μηνύματος του χρήστη μέσα στο πλαίσιο.
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)




# --- Πεδίο Εισαγωγής Μηνύματος Χρήστη (Chat Input) ---
user_query = st.chat_input("Γράψε την ερώτησή σου εδώ...")                        # πλαισιο πληκτρολογησης μνματος χρηστη.Οταν ο χρηστης γραψει κατι και πατησει enter, η συμβολοσειρα αποθηκευεται στο user_query
if user_query:
    # 1. Εμφάνιση ερώτησης χρήστη
    with st.chat_message("user"):
        st.markdown(user_query)                                             # Εμφανίζουν αμέσως την ερώτηση του χρήστη στην οθόνη, πάνω στη ροή της συνομιλίας.

    # 2. Κλήση του Agent Executor περνώντας το ιστορικό συνομιλίας
    with st.chat_message("assistant"):                                      # Ανοίγει το πλαίσιο απάντησης του βοηθού.
        with st.spinner("Σκέφτεται και αναζητά στα έγγραφα..."):                    # σαν εικονιδιο φορτωσης
            try:                                                            # Δοκιμάζει να εκτελέσει την επικοινωνία με τον Agent.
               # Ο Agent περιμένει input και chat_history
               response = agent_executor.invoke({
                   "input" : user_query,
                   "chat_history" : st.session_state.chat_history
               }) 

               ai_response = response["output"]                             # Παίρνουμε την τελική απάντηση που παρήγαγε ο Agent από το λεξικό επιστροφής.
               st.markdown(ai_response)                                     # τυπωουμε την απαντηση σε πλαισιο απαντησης

               #3.Αποθηκευση στο ιστορικο session
               st.session_state.chat_history.append(HumanMessage(content=user_query))         # Προσθέτουμε την ερώτηση του χρήστη στη λίστα ιστορικού συνεδρίας
               st.session_state.chat_history.append(AIMessage(content=ai_response))           # Προσθέτουμε και την απάντηση του AI στη λίστα ιστορικού συνεδρίας (ώστε να είναι διαθέσιμες στην επόμενη ερώτηση).

            except Exception as e:
                st.error(f"Προέκυψε σφάλμα κατά την εκτέλεση του Agent: {e}")