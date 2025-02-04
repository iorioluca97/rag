#!/bin/bash

# Check if poetry is installed
if ! command -v poetry &> /dev/null
then
    echo "Poetry is not installed. Please install poetry first."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
poetry install --no-root

if [ $? -ne 0 ]; then
    echo "Error installing dependencies"
    exit 1
fi

# Run Streamlit
echo "Starting Streamlit..."
poetry run streamlit run main.py
