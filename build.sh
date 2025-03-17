#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Updating system packages..."
sudo apt-get update && sudo apt-get install -y build-essential libffi-dev libssl-dev libev-dev python3-dev

echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Build completed successfully!"
