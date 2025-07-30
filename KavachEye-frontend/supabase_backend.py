from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import cv2
import numpy as np
import os
from datetime import datetime
import json
import hashlib
import jwt
import secrets
from dotenv import load_dotenv
from supabase import create_client, Client
import base64

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')  # Use service key for backend
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuration
JWT_SECRET = secrets.token_hex(32)  # Generate a random secret key

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initialize the database with required tables"""
    try:
        # Tables are created via SQL in Supabase dashboard
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise e

# Global variables for video streams
active_streams = {}

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "KavachEye Backend Server (Supabase)"})

@app.route('/api/stream/start', methods=['POST'])
def start_stream():
    """Start a new video stream"""
    try:
        data = request.get_json()
        stream_id = data.get('stream_id')
        stream_url = data.get('stream_url')
        stream_name = data.get('stream_name', 'Camera Feed')
        
        if not stream_id or not stream_url:
            return jsonify({'error': 'Missing stream_id or stream_url'}), 400
        
        # Store stream info in Supabase
        stream_data = {
            'id': stream_id,
            'name': stream_name,
            'url': stream_url,
            'status': 'active',
            'last_update': datetime.now().isoformat()
        }
        
        # Insert or update stream in Supabase
        result = supabase.table('streams').upsert(stream_data).execute()
        
        active_streams[stream_id] = {
            'url': stream_url,
            'status': 'active',
            'last_update': datetime.now()
        }
        
        return jsonify({
            'status': 'success',
            'message': f'Stream {stream_id} started successfully',
            'stream_id': stream_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream/<stream_id>/frame')
def get_frame(stream_id):
    """Get a frame from a video stream"""
    try:
        if stream_id not in active_streams:
            return jsonify({'error': 'Stream not found'}), 404
        
        stream_info = active_streams[stream_id]
        cap = cv2.VideoCapture(stream_info['url'])
        
        if not cap.isOpened():
            return jsonify({'error': 'Cannot open video stream'}), 500
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return jsonify({'error': 'Cannot read frame'}), 500
        
        # Convert frame to base64
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'status': 'success',
            'frame': f'data:image/jpeg;base64,{frame_base64}',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream/<stream_id>/stop', methods=['POST'])
def stop_stream(stream_id):
    """Stop a video stream"""
    try:
        if stream_id in active_streams:
            del active_streams[stream_id]
        
        # Update stream status in Supabase
        supabase.table('streams').update({
            'status': 'inactive',
            'last_update': datetime.now().isoformat()
        }).eq('id', stream_id).execute()
        
        return jsonify({
            'status': 'success',
            'message': f'Stream {stream_id} stopped successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streams', methods=['GET'])
def list_streams():
    """List all active streams"""
    try:
        # Get streams from Supabase
        result = supabase.table('streams').select('*').execute()
        streams = result.data
        
        return jsonify({
            'status': 'success',
            'streams': streams,
            'active_count': len(active_streams)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alert', methods=['POST'])
def create_alert():
    """Create a new alert"""
    try:
        data = request.get_json()
        
        alert_id = data.get('id')
        alert_type = data.get('type')
        severity = data.get('severity')
        message = data.get('message')
        location = data.get('location')
        
        if not all([alert_id, alert_type, severity, message]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        alert_data = {
            'id': alert_id,
            'type': alert_type,
            'severity': severity,
            'message': message,
            'location': location,
            'timestamp': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Insert alert into Supabase
        result = supabase.table('alerts').insert(alert_data).execute()
        
        return jsonify({
            'status': 'success',
            'message': 'Alert created successfully',
            'alert_id': alert_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def list_alerts():
    """List all alerts"""
    try:
        # Get alerts from Supabase
        result = supabase.table('alerts').select('*').order('timestamp', desc=True).execute()
        alerts = result.data
        
        return jsonify({
            'status': 'success',
            'alerts': alerts
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alert/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert"""
    try:
        # Update alert status in Supabase
        supabase.table('alerts').update({
            'status': 'resolved',
            'resolved_at': datetime.now().isoformat()
        }).eq('id', alert_id).execute()
        
        return jsonify({
            'status': 'success',
            'message': f'Alert {alert_id} resolved successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['id', 'first_name', 'last_name', 'email', 'password', 'id_number', 'department']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user already exists
        existing_user = supabase.table('users').select('*').eq('email', data['email']).execute()
        if existing_user.data:
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Hash password
        hashed_password = hash_password(data['password'])
        
        user_data = {
            'id': data['id'],
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'email': data['email'],
            'password': hashed_password,
            'id_number': data['id_number'],
            'department': data['department'],
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Insert user into Supabase
        result = supabase.table('users').insert(user_data).execute()
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'user_id': data['id']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Hash the provided password
        hashed_password = hash_password(password)
        
        # Check user credentials in Supabase
        result = supabase.table('users').select('*').eq('email', email).eq('password', hashed_password).execute()
        
        if not result.data:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        user = result.data[0]
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user['id'],
            'email': user['email'],
            'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
        }, JWT_SECRET, algorithm='HS256')
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'email': user['email'],
                'department': user['department']
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    """Health check endpoint"""
    try:
        # Test Supabase connection
        result = supabase.table('users').select('count', count='exact').execute()
        
        return jsonify({
            'status': 'healthy',
            'message': 'KavachEye Backend Server is running',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': 'Database connection failed',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting KavachEye Backend Server (Supabase) on port {port}")
    print(f"Supabase URL: {SUPABASE_URL}")
    
    app.run(host='0.0.0.0', port=port, debug=False)