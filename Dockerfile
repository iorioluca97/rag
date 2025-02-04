# Usa un'immagine base con Python preinstallato
FROM python:3.11

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file di progetto nella directory di lavoro
COPY . /app

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Espone la porta di Streamlit (8501 di default)
EXPOSE 8501

# Comando per avviare l'app Streamlit
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
