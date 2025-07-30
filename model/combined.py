from flask import Flask, render_template, Response, request, jsonify
import base64
import os
import time
import json
import random

app = Flask(__name__)
from flask_cors import CORS
CORS(app, origins=['http://127.0.0.1:5500', 'http://localhost:5500', 'http://localhost:3000', 'http://127.0.0.1:3000', '*'], 
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'])

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return jsonify({
        "status": "running", 
        "message": "KavachEye AI Model Service (Vercel)",
        "endpoints": ["/predict", "/status", "/health"]
    })

@app.route('/test')
def test():
    return jsonify({"message": "AI Model service is working!"})

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "KavachEye AI Model Service",
        "deployment": "vercel",
        "timestamp": time.time()
    })

@app.route('/predict', methods=['OPTIONS'])
def handle_preflight():
    """Handle CORS preflight requests"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/predict', methods=['POST'])
def predict():
    """Handle AI prediction requests from frontend"""
    try:
        # Get image data from request
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Process frame with simulated AI models
        results = process_frame_with_simulated_ai()
        
        # Return results in expected format
        response = jsonify({
            'status': 'success', 
            'results': results,
            'timestamp': time.time()
        })
        
        # Add CORS headers
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        
        return response
        
    except Exception as e:
        print(f"Error in predict endpoint: {e}")
        return jsonify({'error': str(e)}), 500

def process_frame_with_simulated_ai():
    """Process frame with simulated AI models for Vercel deployment"""
    results = {
        'pose_detection': {'detected': random.choice([True, False]), 'confidence': random.uniform(0.6, 0.95)},
        'gender_detection': {'detected': random.choice([True, False]), 'gender': random.choice(['Male', 'Female']), 'confidence': random.uniform(0.7, 0.9)},
        'violence_detection': {'detected': random.choice([True, False]), 'classification': random.choice(['Normal', 'Violence']), 'confidence': random.uniform(0.5, 0.85)},
        'face_detection': {'detected': random.choice([True, False]), 'faces_count': random.randint(0, 3)}
    }
    
    return results

@app.route('/status')
def status():
    return jsonify({
        "status": "operational",
        "service": "KavachEye AI Model Service",
        "deployment": "vercel",
        "models": "simulated (for Vercel deployment)",
        "timestamp": time.time()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
