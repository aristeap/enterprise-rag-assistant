#Σε αυτο το αρχειο θα φτιαξουμε τον AI agent (χρησιμοποιώντας LangChain / LangGraph) o οποιος θα συνδιαζει δυο πραγματα:
#   1.Το RAG Retriever: Για να ψάχνει στις πληροφορίες των εγγράφων (κείμενα, πολιτικές) που αποθηκεύσαμε στη Supabase.
#   2.Τα Tools (Εργαλεία): (π.χ. ένα εργαλείο υπολογιστή/Python execution για να εκτελεί ακριβείς αριθμητικούς υπολογισμούς όταν ο χρήστης ζητάει ποσοστιαίες μεταβολές, αθροίσματα ή στατιστικά από τους πίνακες του Excel ή των PDFs).
#   3.Τον Agent Executor: Που δίνει αυτά τα tools στο LLM (gpt-4o-mini) μαζί με ένα System Prompt, ώστε να ξέρει πότε να τα καλεί.
#Ουσιαστικά, ο Agent θα λειτουργεί σαν το «μυαλό» του συστήματος: θα καταλαβαίνει την ερώτηση του χρήστη και θα αποφασίζει 
#   μόνος του πότε θα κάνει αναζήτηση στη βάση και πότε θα χρησιμοποιήσει τα εργαλεία υπολογισμού.


import os
from typing import List
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool                                               #Μετατρέπει μια απλή συνάρτηση Python σε ένα «εργαλείο» που το LLM μπορεί να διαβάσει, 
                                                                                    #       να καταλάβει πότε πρέπει να το καλέσει και να το χρησιμοποιήσει αυτόνομα.
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent


from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.vectorstore import SupabaseVectorStoreManager

load_dotenv()


class EnterpriseAgentManager:
    def __init__(self):
        # 1. Αρχικοποιούμε το LLM μας (π.χ. gpt-4o-mini)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # 2. Παίρνουμε τον retriever από το vectorstore manager μας
        vector_manager = SupabaseVectorStoreManager()
        self.retriever = vector_manager.get_retriever(k=5)


    def setup_tools(self) -> List:
        """
        Ορίζουμε τα Custom Tools που θα έχει στη διάθεσή του ο Agent.
        """

        # --- Tool 1: Αναζήτηση στα έγγραφα (RAG) --- RAG Retriever
        @tool
        def search_documents(query: str) -> str:
            #ΑΥΤΟ ΔΕΝ ΕΙΝΑΙ ΣΧΟΛΙΟ για τον προγραμματιστη αλλα το διαβαζει το LLM. Το LLM διαβάζει αυτή την περιγραφή για να καταλάβει πότε πρέπει να επιλέξει να καλέσει αυτό το εργαλείο.
            """
            Αναζητά σχετικές πληροφορίες, πολιτικές, δεδομένα ή πίνακες 
            μεσα στα αποθηκευμένα έγγραφα (PDFs, Excel, PPTX, Markdown).
            Χρησιμοποίησε αυτό το εργαλείο όταν ο χρήστης ρωτάει κάτι για τα αρχεία.
            """
            docs = self.retriever.invoke(query)                                             #ολα τα σχετικα, με το ερωτημα του χρηστη chunks, που θα παρει το μοντελο για να μπορεσει να απαντησει την ερωτηση του χρηστη
            #μοιαζουν ετσι ομως >
            #docs = 
            #[
            #    Document(
            #        page_content="Οι εργαζόμενοι πλήρους απασχόλησης δικαιούνται 25 ημέρες ετήσιας άδειας.",
            #        metadata={"source": "hr_policies.pdf", "page": 4}
            #    ),
            #    Document(
            #        page_content="Το επίδομα αδείας καταβάλλεται τον Ιούλιο κάθε έτους.",
            #        metadata={"source": "benefits.xlsx", "sheet": "Bonus"}
            #    ),
            
            #αρα θα τα μετατρεψουμε 
            # Ενώνουμε τα περιεχόμενα των εγγράφων σε ένα ενιαίο string για το LLM (βγαζει περιτυλιγματα Document, metadata, κλπ) και κραταει ενα τελικο string>
            #context = 
            #Οι εργαζόμενοι πλήρους απασχόλησης δικαιούνται 25 ημέρες ετήσιας άδειας.
            #Το επίδομα αδείας καταβάλλεται τον Ιούλιο κάθε έτους.
            #Για αιτήσεις αδείας άνω των 5 ημερών απαιτείται έγκριση διευθυντή.
            context = "\n\n".join([doc.page_content for doc in docs])                   #με τα /n καταλαβαινει οτι προκεται για διαφορετικα κομματια 
            return context


        # --- Tool 2: Μαθηματικός Υπολογιστής ---
        @tool
        def calculate_math(expression: str) -> str:
            """
            Εκτελεί ακριβείς μαθηματικές πράξεις ή υπολογισμούς ποσοστιαίων μεταβολών.
            Δώσε μια έγκυρη μαθηματική έκφραση σε Python (π.χ. '(150 - 100) / 100 * 100').
            Χρησιμοποίησε αυτό το εργαλείο για αριθμητικούς υπολογισμούς από πίνακες Excel.
            """
            try:
                result = eval(expression, {"__builtins__": {}}, {})                     #eval:παίρνει ένα string κειμένου (π.χ. "(10 + 20) * 2") και το εκτελεί σαν κανονικό κώδικα/μαθηματική πράξη.
                                                                                        # {"__builtins__": {}}, {}:Η απλή eval() στη Python είναι επικίνδυνη αν της δώσεις τυχαίο κείμενο από έναν χρήστη, διότι θα μπορούσε κάποιος να γράψει κακόβουλο κώδικα (π.χ. να σβήσει αρχεία).
                                                                                        #   αρα με αυτα τα ορισματα 'κλειδωνουμε΄ ' την eval να κανει μονο βασικους μαθηματικους υπολογισμους
                return str(result)                                                      #παιρνει νουμερο της πραξης και το μετατρεπει πισω σε string για να το δωσει στον Agent
            except Exception as e:
                return f"Σφάλμα στον υπολογισμό: {e}"    
        
        return [search_documents, calculate_math]

    #3.  Agent Executor:
    def get_agent_executor(self):   
        """
        Δημιουργεί και επιστρέφει τον Agent Executor συνδέοντας το LLM, τα Tools και το Prompt.
        """
        tools = self.setup_tools()                                                      #πριν ξεκινησουμε να φτιαχνουμε τον agent μαζευουμε σε μια λιστα τα εργαλεια μας για να του τα δωσουμε 

        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "Είσαι ένας κορυφαίος Enterprise AI Assistant ειδικευμένος σε ανάλυση πολυτροπικών εγγράφων (PDF, Excel, PPTX, MD). "
             "Έχεις στη διάθεσή σου εργαλεία αναζήτησης στα έγγραφα και υπολογισμού. "
             "Χρησιμοποίησε τα εργαλεία αυτά πάντοτε όταν χρειάζεται για να δώσεις ακριβείς και τεκμηριωμένες απαντήσεις. "
             "Αν η απάντηση δεν υπάρχει στα έγγραφα, πες το ειλικρινά.\n\n"
             "### Οδηγίες Ανάλυσης Πινάκων & Excel (HTML Tables):\n"
             "1. Όταν διαβάζεις πίνακες δεδομένων (HTML), εξέταζε ΠΑΝΤΑ προσεκτικά τις επικεφαλίδες (<thead>) και τις γραμμές (<tbody>) "
             "ώστε να αντιστοιχίζεις κάθε νούμερο ακριβώς στη σωστή στήλη και κατηγορία.\n"
             "2. Πρόσεξε ιδιαίτερα να μην συγχέεις γενικά κόστη, αθροίσματα ή τριμηνιαία μεγέθη με βασικές παραμέτρους μονάδας "
             "(όπως μέσους μισθούς, ποσοστά margin ή βασικές τιμές ανά κεφάλι).\n"
             "3. Επαλήθευε τους υπολογισμούς και τις τιμές πριν καταλήξεις στην τελική απάντηση."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Δημιουργία του Tool Calling Agent
        agent = create_tool_calling_agent(self.llm, tools, prompt)                                                  #Αυτός ο Agent ξέρει πώς να διαβάζει τις περιγραφές των εργαλείων και να αποφασίζει πότε, με ποια παράμετρο και με ποια σειρά πρέπει να τα καλέσει
        
        # Δημιουργία του Executor που διαχειρίζεται την εκτέλεση(ο AgentExecutor στελνει την ερωτηση στο LLM>λαμβανει εντολη κλησης εργαλειου>εκτελει το εργαλειο>ξαναδινει το αποτελεσμαπισω στο LLM μεχρι να παραχθει η τελικη απαντηση)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)                                      #ο agent απο μονος του είναι απλώς μια «λογική σκέψης».Χρειάζεται έναν Executor (Εκτελεστή) για να τρέξει πραγματικά την αλυσίδα.                       

        return agent_executor

        
