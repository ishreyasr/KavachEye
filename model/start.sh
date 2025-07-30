#!/usr/bin/env bash
# Start script for Render deployment

echo "Starting KavachEye AI Model Service..."

# Set environment variables
export RENDER=true
export PORT=$PORT

# Run the application
python combined.py