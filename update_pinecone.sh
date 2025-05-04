#!/bin/bash
# Script to update Pinecone SDK to v6.0.2 and ensure all dependencies are installed

# Activate the Python 3.11 virtual environment
source venv311/bin/activate

# Uninstall any previous versions of pinecone-client or pinecone
echo "Uninstalling previous pinecone packages..."
pip uninstall -y pinecone-client pinecone

# Install Pinecone SDK v6.0.2
echo "Installing Pinecone SDK v6.0.2..."
pip install pinecone==6.0.2

# Install other required packages
echo "Installing other required packages..."
pip install pytest matplotlib folium scikit-learn

# Install the package in development mode
echo "Installing package in development mode..."
pip install -e .

# Show installed version
echo "Installed Pinecone version:"
pip show pinecone | grep Version

echo "Pinecone SDK update complete. Version 6.0.2 is now installed."
