# 1. Επίσημο, σταθερό Python base image
FROM python:3.12-slim

# Αποτροπή δημιουργίας .pyc αρχείων και άμεση εμφάνιση logs στην κονσόλα
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 2. Εγκατάσταση system dependencies (Poppler, Tesseract OCR, libmagic)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Ορισμός φακέλου εργασίας
WORKDIR /app

# 3. Αντιγραφή και εγκατάσταση Python βιβλιοθηκών (Layer Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Αντιγραφή του υπόλοιπου κώδικα
COPY . .

# 5. Δημιουργία non-root χρήστη για ασφάλεια
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Άνοιγμα της πόρτας του Streamlit
EXPOSE 8501

# 6. Εντολή εκκίνησης της εφαρμογής
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]