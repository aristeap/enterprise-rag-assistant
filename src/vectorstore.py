#στο αρχειο αυτο θα κανουμε :
#   chunking => τα elements μπορεί να είναι πολύ μεγάλα ή πολύ μικρά. Χρησιμοποιούμε τη συνάρτηση chunk_by_title της unstructured για να τα «κόψουμε» έξυπνα.
#   metadata-cleaning & Langchain conversion => θα σβησουμε πραγματα οπως languages etc
#   Embedding & Storage => Τα περνάμε από το OpenAI Embeddings model (text-embedding-3-small) και τα αποθηκεύουμε στον πίνακα της Supabase (NOTE: στα μαθηματα Deeplearning χρησιμοποιησουεμ την διανυσματικη βαση 
#                               chromaDB που ειναι τοπικη βαση αλλα τρ για production θα χρησ. την supabase(pgvector) αντι για chromaDb(vectorstore))

import os
from typing import List
from dotenv import load_dotenv
from unstructured.chunking.title import chunk_by_title
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore, utils         #pabaseVectorStore: Η κλάση-γέφυρα του LangChain που επιτρέπει στην Python να στέλνει και να
                                                                                        #       διαβάζει διανύσματα απευθείας από τη βάση δεδομένων PostgreSQL / pgvector της Supabase
from supabase import create_client, Client


class SupabaseVectorStoreManager:
    def __init__(self, table_name: str = "documents"):                              #οριζει απο default να αποθηκευονται τα δεδομενα σε πινακα documents
        """
        Αρχικοποιεί τη σύνδεση με τη Supabase και το μοντέλο Embeddings.
        """
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.table_name = table_name

        #αν λειπουν τα credentials πεταει σφαλμα τυπου ValueError
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Τα SUPABASE_URL και SUPABASE_SERVICE_KEY πρέπει να οριστούν στο .env!")
        
        #δημιουργια συνδεσης με supabase 
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Ορισμός του μοντέλου embeddings της OpenAI
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


    #η μεθοδος αυτη τρεχει μια φορα οταν θελουμε να βαλουμε τα αρχεια απο το φακελο data στη διανυσματικη βαση του supabase
    def create_vectorstore(self, raw_elements: list) -> SupabaseVectorStore:
        """
        Εφαρμόζει τα Βήματα 3 και 4 από τις σημειώσεις του Deeplearning AI :
        1. Chunking με chunk_by_title
        2. Μετατροπή σε LangChain Documents + καθαρισμός metadata (languages κ.λπ.)
        3. Αποθήκευση στη Supabase (pgvector)
        """ 
        # --- ΒΗΜΑ 3: Τεμαχισμός (Chunking) ---
        elements = chunk_by_title(raw_elements)

        #Μετατρέπουμε σε LangChain Documents και καθαρισμος metadata
        documents = []
        for element in elements:
            metadata = element.metadata.to_dict()
            
            if "languages" in metadata:
                del metadata["languages"]                                                               #Καθαρισμός σύνθετων τύπων (όπως το languages) για να μην σκάσει η βάση 

            metadata["source"] = metadata.get("filename", "unknown")                                    #δημιουργει ενα νεο κλειδι με ονομα source και βαζει μεσα το filename
            documents.append(
                    Document(page_content=element.text, metadata=metadata)                                  #δημιουργει ενα αντικειμενο Document τυπου langchain  κλπ (προηγουμενο μαθημα)     
                )                                                  
            
            #Τι περιεχει το element.metadata.to_dict() πχ για το πρωτο στοιχειο>
            #{'filename': 'donut_paper.pdf',
            # 'filetype': 'application/pdf',
            # 'languages': ['eng'],
            # 'page_number': 1}


        # --- ΒΗΜΑ 4: Vector DB & Storage (Αντί για Chroma, χρησιμοποιούμε Supabase) ---
        print(f"Αποθήκευση {len(documents)} εγγράφων στη Supabase pgvector...")

        #αυτο αποθηκευει τα αρχεια στη βαση 
        vectorstore = SupabaseVectorStore.from_documents(
            documents,
            self.embeddings,
            client = self.client,
            table_name = self.table_name,
            query_name="match_documents"                                                            #δηλώνει το όνομα της SQL συνάρτησης (RPC function) που έχουμε φτιάξει στη Supabase για να κάνει αναζήτηση ομοιότητας (cosine similarity).
        )

        print("Η αποθήκευση ολοκληρώθηκε επιτυχώς!")
        return vectorstore

    def get_retriever(self, k:int = 6):
        """
        Δημιουργεί τον Retriever (όπως ακριβώς στις σημειώσεις Deeplearning), 
        που θα αναζητά τα k πιο σχετικά chunks από τη Supabase.
        """

        #αυτο δεν ξαναστελνει ΤΙΠΟΤΑ στη βαση,Το μόνο που κάνει είναι να δημιουργήσει ένα «αντικείμενο-οδηγό» (reader object) το οποίο γνωρίζει πώς να συνδεθεί στον πίνακα της
        #        Supabase για να κάνει αναζητήσεις (queries)
        vectorstore = SupabaseVectorStore(
            client=self.client,
            embedding=self.embeddings,
            table_name=self.table_name
        )

        #τι είναι: Είναι ο «μηχανισμός αναζήτησης» που ρυθμίζουμε πάνω στη supabase vector database.
        #   : Όταν ο χρήστης υποβάλλει μια ερώτηση ο retriever μετατρεπει την ερωτηση σε ΔΙΑΝΥΣΜΑ, και μτ αναλαμβάνει να ψάξει στη βάση δεδομένων, 
        #   να συγκρίνει το διάνυσμα της ερώτησης με τα διανύσματα των αποθηκευμένων chunks, και να ανακτήσει (retrieve) τα 6 πιο σχετιζόμενα κομμάτια κειμένου
        #   (π.χ. τα $6$ πιο κοντινά, k=6). Αυτά τα κομμάτια θα δοθούν τελικά ως context στο LLM για να απαντήσει.
        return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})
                                                                                        
       