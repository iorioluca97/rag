from typing import Dict, List
import unicodedata
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
import numpy as np
from pymongo import MongoClient
from pymongo.server_api import ServerApi
# from langchain.embeddings import OpenAIEmbeddings
# from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from config.logger import logger


load_dotenv()

class MongoDb:
    def __init__(self, 
                 uri: str = os.environ.get('MONGODB_ATLAS_CLUSTER_URI'), 
                 database_name: str = "mydatabase", 
                 collection_name: str = "mycollection",
                 recreate_collection: bool = False
                 ):
        if not uri:
            raise ValueError("MongoDB URI is not set in environment variables")
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.embedding_model = OpenAIEmbeddings()

        self.ping()

        self.database_name = self.client[database_name]

        if recreate_collection:
            if collection_name in self.database_name.list_collection_names():
                self.client[database_name].drop_collection(collection_name)

        self.collection = self.database_name[collection_name]
        logger.info(f"Connected to the collection '{collection_name}' in the database '{database_name}'")

    def ping(self):
        # Send a ping to confirm a successful connection
        try:
            self.client.admin.command('ping')
            logger.debug("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            logger.error(e)
    
    def collection_exists(self, collection_name: str) -> bool:
        if collection_name in self.database_name.list_collection_names():
            logger.info(f"Collection '{collection_name}' already exists")
            return True
        logger.info(f"Collection '{collection_name}' does not exist")
        return False
    
    def change_collection(self, collection_name: str):
        self.collection = self.database_name[collection_name]
        logger.info(f"Changed to collection '{collection_name}'")

    def __getattr__(self, name):
        """
        Intercepts attribute access and delegates it to the MongoDB collection instance.
        """
        if hasattr(self.collection, name):
            return getattr(self.collection, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    

    def query_with_keyword_filter(
        self,
        query_text: str, 
        top_k: int = 5, 
        keyword_filter: List[str] = None):
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.embed_query(query_text.lower())

            # Cosine similarity function
            def cosine_similarity(vec1, vec2):
                return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

            # Get unique pages and their best matching segments
            page_scores = {}  # Dictionary to store best score per page

            # Get all documents
            all_documents = list(self.collection.find({}))

            # Apply keyword filter if provided
            if keyword_filter:
                filtered_documents = [doc for doc in all_documents if any(kw.lower() in doc.get("keywords", []) for kw in keyword_filter)]
                documents_to_process = filtered_documents if filtered_documents else all_documents
            else:
                documents_to_process = all_documents

            # Process each document
            for doc in documents_to_process:
                page = doc["page"]
                score = cosine_similarity(query_embedding, np.array(doc["embedding"]))
                
                # Update page_scores if this is a better match for the page
                if page not in page_scores or score > page_scores[page]["score"]:
                    page_scores[page] = {
                        "text": doc["text"],
                        "score": score
                    }

            # Convert to list and sort by score
            results = [
                {
                    "page": page,
                    "text": data["text"],
                    "score": data["score"]
                }
                for page, data in page_scores.items()
            ]
            
            # Sort by score and get top_k
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]

        except Exception as e:
            print(f"Errore durante l'esecuzione della query: {e}")
            return []
        

        
    def process_and_store_pages(
            self,
            path: str, 
            keywords: Dict[int, List[str]]
            ):
        """
        Process and store pages in the MongoDB database with their embeddings and keywords.

        Args:
            service_dir (str): Directory where the files are located.
            keywords (Dict[int, List[str]]): Dictionary mapping page numbers to keywords.
            db: MongoDB collection instance for storing documents.
            embedding_model: Model instance for generating embeddings.
        """
        service_dir = path.split("/")[-1].split(".pdf")[0].lower().replace("/", "_").replace("\\", "_")
        for x, filename in enumerate(sort_files(os.listdir(f'extracted_pages/{service_dir}'))):
            try:
                # Open and read the file content
                with open(f"extracted_pages/{service_dir}/{filename}", "r", encoding="utf-8") as file:
                    data = file.read()

                # Clean the text
                cleaned_data = clean_text(data)

                # Extract keywords for the current page
                page_keywords = sorted(keywords.get(x, []))

                # Generate embedding for the document
                embedding = self.embedding_model.embed_documents([cleaned_data])[0]

                # Insert document into the database
                self.insert_one({
                    "page": x,
                    "text": cleaned_data,
                    "embedding": embedding,
                    "keywords": page_keywords,
                    "filename": f"extracted_pages/{service_dir}/{filename}"
                })

                logger.info(f"Processed: {filename} (Page {x})")
            except Exception as e:
                logger.error(f"Error processing {filename} (Page {x}): {e}")


# Ordina i file per numero di pagina
def sort_files(files: List[str]) -> List[str]:
    def extract_page_number(filename):
        return int(filename.replace('page_', '').replace('.txt', ''))
    
    return sorted(
        files,
    key=extract_page_number
    )

def clean_text(text):
    """
    Rimuove i caratteri speciali e normalizza il testo.
    """
    # Rimuove caratteri non stampabili
    text = ''.join(char for char in text if char.isprintable())
    # Normalizza il testo (elimina accenti e caratteri speciali)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    # Rimuove spazi extra
    text = ' '.join(text.split())
    return text



