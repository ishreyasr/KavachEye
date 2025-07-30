#!/usr/bin/env bash
# Build script for Render deployment

echo "Starting build process..."

# Install system dependencies for OpenCV
apt-get update
apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs

echo "Build completed successfully!" 