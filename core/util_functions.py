import os
from dotenv import load_dotenv
import yaml
from config.cfg import AGENTS_DIR, MAX_HISTORY_TOKENS
import re
import json
import os
from typing import List
import nltk
from nltk.corpus import stopwords
from config.logger import logger

def laod_env():
    load_dotenv()
    if os.environ.get("OPENAI_API_KEY") is None:
        raise ValueError("API KEY NOT FOUND")
    if os.environ.get("MONGODB_ATLAS_CLUSTER_URI") is None:
        raise ValueError("MONGODB URI NOT FOUND")



def process_question(text: str) -> str:
    nltk.download('stopwords', quiet=True)
    
    # Obtain the Italian stopwords
    stop_words = set(stopwords.words('italian'))
    
    # Convert text to lowercase
    text = text.lower()
    
    # Remove stopwords
    words = [word for word in text.split() if word not in stop_words]
    
    # Remove special characters
    processed_text = " ".join(words)
    processed_text = re.sub(r'[^a-zA-Z0-9\s]', '', processed_text)
    
    return processed_text




def load_service_data(service_dir: str) -> str:
    try:
        with open(os.path.join(AGENTS_DIR, service_dir + '.yaml'), "r") as file:
                agent_data = yaml.safe_load(file)
        return agent_data['prompt']['context']
    except Exception as e:
        logger.warning(f"Error loading service data: {e}")
        return "Nessuna informazione disponibile"



def call_llm_for_question(
        path: str,
        question: str, 
        external_knowledge: str, 
        client, 
        model: str = 'gpt-4-turbo', 
        temperature: float = 0.5,  
        top_p: float = 0.95, 
        max_tokens: int = 4000,
        user_type: str = "PM",
        history: List[str] = None
    ):

    def get_user_type(user_type):
        if user_type == "PM":
            return "un Product Manager con poca o nessuna conoscenza tecnica"
        else:
            return "un utente tecnico con conoscenze avanzate in ambito informatico"

    service_dir = path.split("/")[-1].split(".pdf")[0].lower().replace("/", "_").replace("\\", "_")


    # print("Message history: ",refactor_history(truncate_history(history, MAX_HISTORY_TOKENS)))

    # Costruzione del payload
    payload = {
        "messages": [
            {
                "role": "system",
                "content": f"""
                Sei un assistente esperto e professionale, specializzato nel servizio "{service_dir}".
                Il tuo interlocutore è {get_user_type(user_type)}. 

                Rispondi nella lingua usata dall'utente.

                Il tuo compito è rispondere in modo chiaro, conciso e informativo, adattando il tuo linguaggio al livello di conoscenza dell'utente.

                Ecco le informazioni principali che conosci sul servizio "{service_dir}":
                {load_service_data(service_dir)}

                Usa queste informazioni come base per rispondere alle domande dell'utente.
                Se non hai abbastanza informazioni nella tua knowledge base, utilizza le informazioni fornite dall'utente o comunica chiaramente che non puoi rispondere.
                """
                },

                {
                                "role": "user",
                                "content": f"""
                Data la domanda dell'utente: 
                {question}

                Data la conversazione precedente:
                {refactor_history(truncate_history(history, MAX_HISTORY_TOKENS))}

                Date le informazioni estratte dal documento correlato:
                {external_knowledge}

                Fornisci una risposta dettagliata ma comprensibile per l'utente. Se necessario, includi esempi pratici o spiegazioni semplici per rendere la tua risposta più utile.
                
                RISPONDI IN INGLESE.
                """
            },
        ],
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
    }


    with open("./chatbot_output/payload.json", "w") as file:
        json.dump(payload, file, ensure_ascii=False, indent=4)

    # Richiesta al modello
    response = client.chat.completions.create(model=model, messages=payload["messages"], max_tokens=max_tokens, stream=True)

    # Streaming della risposta
    for chunk in response:
        if chunk is not None and chunk.choices:
            content = chunk.choices[0].delta.content
            if content is not None:
                yield content
    



def call_llm_for_toc(
        path: str,
        client, 
        model: str = 'gpt-4o', 
        temperature: float = 0.5,  
        top_p: float = 0.95, 
        max_tokens: int = 8000
    ) -> tuple:
    """
    Chiamata al modello di linguaggio per estrarre la Table of Contents (ToC).
    
    Args:
        text (str): Il testo estratto dal PDF.
        client: Il client per interagire con il modello di linguaggio.
        model (str): Modello da utilizzare per la chiamata (default: 'gpt-4o').
        temperature (float): Temperatura per la generazione del testo.
        top_p (float): Nucleus sampling.
        max_tokens (int): Numero massimo di token da generare.

    Returns:
        tuple: Una tupla contenente due liste: 
            - toc: Lista di dizionari con "title" e "page".
            - pages: Lista delle pagine dove è stata trovata la ToC.
    """
    service_dir = path.split("/")[-1].split(".pdf")[0].lower().replace("/", "_").replace("\\", "_")
    text = get_first_pages_text(service_dir)


    # Costruzione del payload per la richiesta
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "Sei un AI esperto in analisi di documenti."
            },
            {
                "role": "user",
                "content": (
                    f"""
                    Dato il testo estratto dal pdf, il tuo compito è estrarre l'Indice.
                    Devi rispondere CON UN DIZIONARIO dove la chiave sarà una stringa
                    composta dai numeri di pagina in cui hai trovato l'Indice, e il valore
                    sarà una LISTA contenente i titoli e le pagine di ogni capitolo.
                    
                    L'output deve essere SOLO il dizionario richiesto nel seguente formato,
                    in modo da poter essere facilemente caricato come dizionario python:
                    
                    "{{ "pagine_indice" : [
                        {{"title": "Capitolo 1", "page": 1}},
                        {{"title": "Capitolo 2", "page": 2}},
                        ...
                    ]}}"
                    

                    Di seguito il testo estratto:
                    {text}
                    """
                )
            }
        ],
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens
    }

    
    logger.debug("Payload: {}".format(payload))
    response = client.chat.completions.create(model=model, messages=payload["messages"], max_tokens=max_tokens)

    return validate_answer(response.choices[0].message.content)





def refactor_history(history):
    str_history = ""
    if history is None:
        return str_history
    else:
        for elem in history:
            str_history += elem.get('role', '').upper() + ": " + elem.get('content', '') + "\n"
        return str_history            

def truncate_history(history, max_tokens):
    # Calcola la lunghezza e taglia i messaggi più vecchi
    current_tokens = 0
    truncated_history = []
    for msg in reversed(history):
        msg_tokens = len(msg['content'].split())  # Stima dei token
        if current_tokens + msg_tokens > max_tokens:
            break
        truncated_history.insert(0, msg)
        current_tokens += msg_tokens
    return truncated_history



def get_first_pages_text(service_dir: str) -> str:
    full_text = ""  
    for page in range(1, 6):
        with open(f"extracted_pages/{service_dir}/page_{page}.txt", "r", encoding="utf-8") as file:
            data = file.read()
            full_text += "\n PAGE NUMBER " + str(page) + "\n" + data
    return full_text

def validate_answer(res: dict) -> tuple:
    if 'json' in res[:10] or 'python' in res[:10] or 'dict' in res[:10]:
        cleaned = res.replace('json', '').replace('python', '').strip().replace("```", "")
    _ = json.loads(cleaned)

    # Get the pages
    try:
        pages = list(_.keys())[0].split(",")
    except:
        pages = []
    # Get the ToC
    try:
        toc = _[list(_.keys())[0]]
    except:
        toc = []

    return toc, pages

