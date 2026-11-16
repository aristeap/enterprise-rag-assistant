#In this file the parsing of the uploaded files will happen in order to ger back their elements (the files will be in the data folder)
#   -> PDF/Tables : unstructured library,yolox model with hi_res
#   -> Excel (.xlsx), : Pandas in order to convert the tables in text
#   ->PPTX, : partition_pptx
#   -> MD  : partition_md


import os
import pandas as pd
from openai import OpenAI
from typing import List
from unstructured.partition.md import partition_md
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.pptx import partition_pptx
from unstructured.documents.elements import Element, Table
from dotenv import load_dotenv

load_dotenv()



class DocumentIngestionPipeline:
    #ο constructor της κλασης, θα παιρνει τα αρχεια που θελουμε να κανουμε parsing απο τον φακελο data ως default
    #data_dir: str = "data" -> το ορισμα που περιμενουμε ειναι τυπου string και εχει default value το data
    def __init__(self, data_dir: str = "data"):
        """
        Επεξεργάζεται το PDF τοπικά με hi_res, yolox και table structure inference.
        Ο λογος που πηγα σε τοπικες λυσεις ειναι οτι το Unstructured API ηθελε work email 
        """
        self.data_dir = data_dir
        self.client = OpenAI()                                       # Χρησιμοποιεί το OPENAI_API_KEY για τα summaries των excel tables 
       

    def load_complex_pdf(self, file_path: str) -> List[Element]:
        """
        Επεξεργάζεται πολύπλοκα PDF με tables χρησιμοποιώντας hi_res, yolox 
        και table structure inference.
        """
        pdf_elements = []
        try:
            filename = os.path.basename(file_path)
            print(f"📄 Τοπική επεξεργασία PDF (hi_res + yolox): {file_path}...")

            pdf_elements=partition_pdf(
                filename=file_path,
                strategy="hi_res",
                hi_res_model_name="yolox",
                pdf_infer_table_structure=True,
                skip_infer_table_types=[],
            )
            
            # --- Θα πάρουμε την HTML των πινάκων ---
            for el in pdf_elements:
                if el.category == "Table":
                    html_content = getattr(el.metadata, "text_as_html", None)
                    if html_content:
                        el.text = f"[TABLE HTML]\n{html_content}\n[/TABLE HTML]"

            # --- Καθαρισμός Μεταδεδομένων (Headers & References) ---
            pdf_elements = [el for el in pdf_elements if el.category != "Header"]
            ref_titles = [el for el in pdf_elements if el.text == "References" and el.category == "Title"]
            if ref_titles:
                ref_id = ref_titles[0].id
                pdf_elements = [el for el in pdf_elements if el.metadata.parent_id != ref_id]

            print(f"✅ Επιτυχές parsing του PDF '{os.path.basename(file_path)}': {len(pdf_elements)} elements.")

        except Exception as e:
            print(f"❌ Σφάλμα στο load_complex_pdf: {e}")

        return pdf_elements
  

    #μεθοδος που παιρνει σαν ορισμα ενα file path τυπου str και θα επιστρεψει μια λιστα αντικειμενων τυπου Element
    def load_markdown(self, file_path: str) -> List[Element]:
        """
        Διαβάζει ένα αρχείο Markdown (.md) και επιστρέφει λίστα από unstructured Elements.
        """
        elements = partition_md(filename=file_path)
        return elements


    def load_powerpoint(self, file_path: str) -> List[Element]:
        """
        Διαβάζει ένα αρχείο powerpoint (.pptx) και επιστρέφει λίστα από unstructured Elements.
        """ 
        elements = partition_pptx(filename=file_path)
        return elements


    def _generate_table_summary(self, html_table: str, sheet_name: str, filename: str) -> str:
        """Χρησιμοποιεί το gpt-4o-mini για να δημιουργήσει μια ολοκληρωμένη και περιεκτική περίληψη-ευρετηρίαση του πίνακα."""
        prompt = (
            f"Αυτός είναι ένας πίνακας δεδομένων από το αρχείο '{filename}' και το φύλλο (sheet) '{sheet_name}'. "
            "Παρακαλώ δώσε μια περιεκτική αλλά πλήρη περίληψη του περιεχομένου του πίνακα. "
            "Συμπερίλαβε, ανάλογα με το τι υπάρχει στον πίνακα: "
            "1. Τις βασικές κατηγορίες, οντότητες, προϊόντα ή γραμμές που αναλύονται. "
            "2. Τις στήλες, τις μετρικές, τις τιμές ή τις παραμέτρους που παρουσιάζονται. "
            "3. Τυχόν χρονικές περιόδους, έτη, τρίμηνα ή ημερομηνίες. "
            "4. Το γενικότερο νόημα ή συμπέρασμα που προκύπτει από τα δεδομένα. "
            "Η περίληψη αυτή θα χρησιμοποιηθεί αποκλειστικά για την ακριβή ανεύρεση (semantic search) του πίνακα από RAG σύστημα."
        )
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",                                                                    #οικονομικο και γρηγορο
                messages=[
                    {"role": "system", "content": "Εσείς είστε ένας ειδικός αναλυτής επιχειρησιακών δεδομένων και δομημένης πληροφορίας."},
                    {"role": "user", "content": f"{prompt}\n\nΠίνακας HTML:\n{html_table}"}
                ],
                max_tokens=350,
                temperature=0.0 # Μηδενική θερμοκρασία για σταθερή, ακριβή και γεγονότο-κεντρική περίληψη
            )
            return response.choices[0].message.content.strip()                                          #επιστρεφει την απαντηση του gpt-4o-mini χωρις περιττα κενα στο τελος
        except Exception as e:
            print(f"⚠️ Σφάλμα στη δημιουργία summary πίνακα: {e}")
            return f"Πίνακας από το φύλλο {sheet_name} του αρχείου {filename}."


    def load_excel_as_elements(self, file_path: str) -> List[Element]:
        """
        Διαβάζει το Excel, καθαρίζει τα δεδομένα, παράγει HTML και 
        δημιουργεί LLM summary για κορυφαία ακρίβεια στο Retrieval.
        """
        elements=[]
        filename = os.path.basename(file_path)                              #Παίρνει μόνο το όνομα του αρχείου από όλη τη διαδρομή (π.χ. από το "data/financials/report.xlsx" κρατάει μόνο το "report.xlsx").
        
        try:
            # Διαβάζουμε όλα τα sheets του Excel σε dictionary από DataFrames
            excel_data = pd.read_excel(file_path, sheet_name=None)              #None: διαβαζει ολα τα διαθεσιμα φυλλα/sheets.Επιστρεφει { 'Onoma_Sheet': DataFrame } οπου DataFrame ο πινακας

            for sheet_name, dataframe in excel_data.items():
               #1. Καθαρισμός: Αφαίρεση εντελώς κενών γραμμών/στηλών και αντικατάσταση NaN με κενό string
               df_cleaned = dataframe.dropna(how='all').dropna(axis=1, how='all').fillna("")                       


               if df_cleaned.empty:                                                             #αν το φυλλο(sheet) του excel ειναι εντελως κενο
                continue

               # 2. Παραγωγή HTML
               html_table = df_cleaned.to_html(index=False)                                 #Μετατρέπει το καθαρό DataFrame σε κώδικα HTML (<table>...</table>), 
                                                                                            #   χωρίς να τυπώνει το ανούσιο index αρίθμησης γραμμών της pandas (0, 1, 2...). Έτσι διατηρείται ακέραια η σχέση γραμμής-στήλης
                
                # 3. Παραγωγή LLM Summary για το Vector Search
               print(f"📊 Δημιουργία AI summary για το Excel sheet: {sheet_name} ({filename})...")
               table_summary = self._generate_table_summary(html_table, sheet_name, filename)


               # 4. Συνδυασμός: Η περίληψη μπαίνει στο text για τα embeddings, το HTML στα metadata              
               text_content = (
                   f"File: {filename} | Sheet: {sheet_name}\n"
                   f"--- Table Summary ---\n{table_summary}\n\n"                        #Το Table Summary βοηθάει το Vector Search να βρει το σωστό chunk όταν ρωτάς κάτι με φυσική γλώσσα.
                   f"--- Raw HTML Table ---\n{html_table}"                              #Ο Raw HTML Table δίνει στο τελικό LLM τα ακριβή νούμερα χωρίς απώλειες.
                ) 
               
               # 5. Δημιουργούμε το Unstructured Table element
               table_element = Table(text=text_content)

               # 4. Συμπληρώνουμε τα metadata (συμπεριλαμβανομένου του text_as_html για ομοιομορφία με τα PDFs)
               table_element.metadata.filename = filename
               table_element.metadata.filetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"            #Ορίζει το MIME type του αρχείου Excel στα μεταδεδομένα=είναι ακριβώς η επίσημη, τυπική ονομασία MIME type για τα σύγχρονα αρχεία Excel (.xlsx) που βασίζονται σε XML (από το Microsoft Office 2007 και έπειτα)
               table_element.metadata.text_as_html = html_table

               elements.append(table_element)                                               #Εδώ χρησιμοποιείται .append() επειδή προσθέτουμε ένα μεμονωμένο Table αντικείμενο σε κάθε γύρο του loop)
        except Exception as e:
            print(f"Σφάλμα κατά την ανάγνωση του Excel {file_path}: {e}")

        return elements
            

    
    def process_all_files(self) -> List[Element]:
        """
        Σκανάρει τον φάκελο data/ και καλεί την αντίστοιχη 
        συνάρτηση parsing ανάλογα με την κατάληξη του αρχείου.
        """
        #εδω θα μαζεψουμε τα elements απο ολα τα αρχεια που σαρωσαμε
        all_elements = []

        #Αν δεν υπαρχει φακελος data τον δημιουργουμε >
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)                                           #αν δεν υπαρχει φτιαξτον και εκτυπωσε ενα ενημερωτικο μνμ
            print(f"Ο φάκελος '{self.data_dir}' δημιουργήθηκε. Βάλε τα αρχεία σου εκεί!")
            return all_elements

        
        #διασχιζουμε ολα τα αρχεια του φακελου
        for file_name in os.listdir(self.data_dir):                 #os.listdir(self.data_dir) -> επιστρεφει μια λιστα με ολα τα file names μεσα στο self.data_dir (=/data)
            file_path = os.path.join(self.data_dir, file_name)      #ενωνει το dir που ειμαστε (δηλαδη το data) με το file name (πχ data/policy.md)

            if file_name.endswith(".md"):
               elements = self.load_markdown(file_path)             #καλει την load_markdown για το συγκεκριμενο file_path πχ data/policy.md
               all_elements.extend(elements)                        #extend vs append.Αν ειχα [1,2,3] και ηθελα να βαλω και τα [4,5]. Με το append -> [1,2,3,[4,5]]. Eνω με το extend -> [1,2,3,4,5]

            elif file_name.endswith(".pptx"):
                elements = self.load_powerpoint(file_path)
                all_elements.extend(elements)

            elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
                elements = self.load_excel_as_elements(file_path)
                all_elements.extend(elements)

            elif file_name.endswith(".pdf"):
                elements = self.load_complex_pdf(file_path)
                all_elements.extend(elements)

        return all_elements




