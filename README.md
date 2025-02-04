# PDF Analysis and RAG Chatbot
## Description
This project implements a Retrieval-Augmented Generation (RAG) system using Streamlit, designed to analyze PDF documents and enable intelligent conversations about their content. The application extracts Table of Contents and key terms from PDF files, stores them in a vector database, and allows users to interact with the content through an LLM-powered chatbot.

## Key Features
- PDF document analysis and metadata extraction
- Automatic Table of Contents generation
- Key terms identification and extraction
- Vector database storage for efficient retrieval
- LLM-powered conversational interface
- Relevance scoring for answers
- User feedback system for responses

## Installation
```bash
# Clone the repository
git clone https://github.com/iorioluca97/rag.git

# Navigate to the project directory
cd rag

# Option 1: Install with Poetry (recommended)
sh start_poetry.sh

# Option 2: Install with Virtual Environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Installation with Docker
```bash
docker build -t rag .

docker run -p 8501:8501 rag
```

## Usage
1. Launch the Streamlit application (command will be shown after installation)
2. Upload your PDF file using the upload container in the top-right
3. The system will automatically:
   - Extract and display the Table of Contents in the left sidebar
   - Process and store document metadata in the vector database
   - Display any available FAQs for the document

4. Start a conversation with the chatbot:
   - Ask questions about the document content
   - View relevance scores for each response
   - Provide feedback on answer quality (scale 1-3)
   - See source page references for answers

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
MIT License

Copyright (c) bunhere.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contact
For questions and support, please contact the project maintainers at [Add contact information]

Would you like me to make any additional adjustments to better reflect specific aspects of your project?