#!/bin/bash

# Verifica che Poetry sia installato
if ! command -v poetry &> /dev/null
then
    echo "Poetry non è installato. Installalo e riprova."
    exit 1
fi

# Installa le dipendenze definite in pyproject.toml
echo "Installazione delle dipendenze con Poetry..."
poetry install --no-root

if [ $? -ne 0 ]; then
    echo "Errore durante l'installazione delle dipendenze."
    exit 1
fi

# Esegui l'app Streamlit
echo "Avvio di Streamlit con Poetry..."
poetry run streamlit run main.py
