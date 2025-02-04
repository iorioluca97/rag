import os

# FAQ
FAQ = {
    "similarity_functional_document_24-06-20" : [
        "What is the dispersion parameter in the 'Generic Search' algorithm?",
        "Which input payload is required for the 'Generic Search' algorithm?",
    ],
    "page_split_functional_document_24-05-16" : [
        "What does the anchor and sub-anchor mean in the 'Page Split' algorithm?",
    ]}

# AGENTS DIRECTORY
AGENTS_DIR = "agents" 

# MAXIMUM NUMBER OF HISTORY TOKENS
MAX_HISTORY_TOKENS = 2000

# MAXIMUM NUMBER OF CHARACTERS TO USE
MAX_CHAR_TOC_TO_USE = 10000

# Keywords to find the Table of Contents
TOC_KEYWORDS = ["Indice", "Index", "Table of Contents", "Sommario", "ToC", "Table des Matières", "Inhaltsverzeichnis", "INDEX"]

# KEYWORDS TO IGNORE
DEFAULT_KEYWORDS_TO_IGNORE = [
    "generali",
    "project",
    "[dict]",
    "[bool]",
    "[str/list/dict]",
    "[str/list]",
    "[str/dict]",
    "[list/dict]",
    "[dict/list]",
    "[str]",
    "[string]",
    "[int]",
    "[float]",
    "[list]",
]

REQUIRED_DIRS = [
    'chatbot_output',
    'tmp',
    'extracted_pages',
]