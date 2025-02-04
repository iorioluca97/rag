# Project Name

## Description
A brief description of what this project does and who it's for.

## Installation
Instructions on how to install and set up the project.

```bash
# Clone the repository
git clone https://github.com/iorioluca97/poc_backup.git

# Navigate to the project directory
cd yourproject

# Install dependencies with poetry or by creating a virtual env with python
sh start_poetry.sh

# OR
```bash
python -m venv venv

# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```
```

## Usage
Instructions on how to use the project.
In order to use the chatbot you have to feed a pdf file in the upload container on the top-right of the application. 
The pdf will be extracted and its metadata will be stored in a mongodb collection, in the meanwhile you will able to see on the left side the Table of Contents extracted.

If there are FAQs available for this document they will be shown in the left sidebar, under the section "FAQ".

At this point you can start a conversation, and the llm will answer by its knowledge plus the document knowledge fecthed in the vector db. 

Each answer will make appear the vector scores related to the page retrieved, and a feedback section where the user can rank in a scale from 1 to 3 the llm answer.

```bash
# Run the project
npm start
```

## Contributing
Guidelines for contributing to the project.

# MIT License
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
Contact information for the project maintainer.