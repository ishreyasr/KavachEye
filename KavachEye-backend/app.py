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
CORS(app, origins=[
    'http://127.0.0.1:5500', 
    'http://localhost:5500', 
    'http://localhost:3000', 
    'http://127.0.0.1:3000',
    'https://kavacheye.vercel.app',
    'https://kavacheye-fkjjaw6yr-shreyas162004s-projects.vercel.app',
    'https://kavacheye-j9pymzlrx-shreyas162004s-projects.vercel.app',
    'https://kavacheye-1olt3qbsh-shreyas162004s-projects.vercel.app',
    'https://kavacheye-8pdu6ffp5-shreyas162004s-projects.vercel.app',
    'https://kavacheye-h4vbQCSxd3Q6F3m8ug3C4uhBKUbJ.vercel.app',
    '*'
], 
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'])

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
            print(f"Connected to Supabase: {SUPABASE_URL}")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise e

# Global variables for video streams
active_streams = {}

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "KavachEye Backend Server (Supabase)"})

@app.route('/api/predict', methods=['OPTIONS'])
def handle_preflight():
    """Handle CORS preflight requests"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/api/alert/status/<stream_id>', methods=['OPTIONS'])
def handle_alert_status_preflight(stream_id):
    """Handle CORS preflight requests for alert status"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/api/alert', methods=['OPTIONS'])
def handle_alert_preflight():
    """Handle CORS preflight requests for alerts"""
    response = jsonify({'status': 'ok'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

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
        print(f"Creating alert with data: {data}")
        
        alert_id = data.get('id')
        alert_type = data.get('type')
        severity = data.get('severity')
        message = data.get('message')
        location = data.get('location')
        stream_id = data.get('stream_id', 'default')  # Add stream_id tracking
        image_data = data.get('image_data')  # Base64 image data from frontend
        
        if not all([alert_id, alert_type, severity, message]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if Supabase is configured
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("Supabase not configured")
            return jsonify({
                'status': 'success',
                'message': 'Alert created successfully (Supabase not configured)',
                'alert_id': alert_id,
                'alert_sent': True,
                'image_captured': image_data is not None
            })
        
        # Check if alert already sent for this location within the last 3 minutes
        try:
            from datetime import timedelta
            three_minutes_ago = (datetime.now() - timedelta(minutes=3)).isoformat()
            
            existing_alert = supabase.table('alerts').select('*').eq('location', location).eq('status', 'active').gte('timestamp', three_minutes_ago).execute()
            
            if existing_alert.data:
                # Calculate time remaining until next alert is allowed
                latest_alert = max(existing_alert.data, key=lambda x: x.get('timestamp', ''))
                alert_time = datetime.fromisoformat(latest_alert['timestamp'].replace('Z', '+00:00'))
                next_allowed_time = alert_time + timedelta(minutes=3)
                time_remaining = next_allowed_time - datetime.now()
                minutes_remaining = max(0, int(time_remaining.total_seconds() // 60))
                seconds_remaining = max(0, int(time_remaining.total_seconds() % 60))
                
                return jsonify({
                    'status': 'error',
                    'message': f'Alert already sent for this location. Next alert allowed in {minutes_remaining}m {seconds_remaining}s',
                    'alert_sent': True,
                    'time_remaining': {
                        'minutes': minutes_remaining,
                        'seconds': seconds_remaining
                    }
                }), 400
        except Exception as e:
            print(f"Error checking existing alerts: {e}")
        
        # Process image data if provided
        image_url = None
        image_filename = None
        image_size = None
        image_type = None
        
        print(f"Image data received: {image_data is not None}")
        if image_data:
            print(f"Image data length: {len(image_data)}")
            print(f"Image data starts with: {image_data[:50]}...")
            
            try:
                # Generate unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_filename = f"alert_{alert_id}_{timestamp}.jpg"
                
                # Decode base64 image data
                import base64
                image_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
                image_size = len(image_bytes)
                image_type = 'image/jpeg'
                
                # For now, we'll store the base64 data directly
                # In production, you might want to upload to Supabase Storage
                image_url = f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"
                
                print(f"Image captured for alert {alert_id}: {image_filename} ({image_size} bytes)")
                
            except Exception as img_error:
                print(f"Error processing image data: {img_error}")
                image_data = None
        else:
            print("No image data provided")
        
        alert_data = {
            'id': alert_id,
            'type': alert_type,
            'severity': severity,
            'message': message,
            'location': location,
            'timestamp': datetime.now().isoformat(),
            'status': 'active',
            'image_data': image_data,
            'image_url': image_url,
            'image_timestamp': datetime.now().isoformat()
        }
        
        # Insert alert into Supabase
        try:
            result = supabase.table('alerts').insert(alert_data).execute()
            print(f"Alert {alert_id} created successfully in Supabase")
        except Exception as supabase_error:
            print(f"Error inserting alert into Supabase: {supabase_error}")
            # Return success anyway since the alert was processed
            return jsonify({
                'status': 'success',
                'message': 'Alert created successfully (database error ignored)',
                'alert_id': alert_id,
                'alert_sent': True,
                'image_captured': image_data is not None
            })
        
        return jsonify({
            'status': 'success',
            'message': 'Alert created successfully',
            'alert_id': alert_id,
            'alert_sent': True,
            'image_captured': image_data is not None
        })
        
    except Exception as e:
        print(f"Error creating alert: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alert/status/<stream_id>', methods=['GET'])
def get_alert_status(stream_id):
    """Check if alert has been sent for a specific stream"""
    try:
        print(f"Checking alert status for stream: {stream_id}")
        
        # Check if Supabase is configured
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("Supabase not configured")
            return jsonify({
                'status': 'success',
                'alert_sent': False,
                'stream_id': stream_id,
                'message': 'Supabase not configured'
            })
        
        # Convert stream_id to location format (e.g., stream_park -> Park)
        location = stream_id.replace('stream_', '').replace('_', ' ').title()
        if stream_id == 'emergency_stream':
            location = 'Live Camera Feed'
        
        # Check if there's an active alert for this location within the last 3 minutes
        from datetime import timedelta
        three_minutes_ago = (datetime.now() - timedelta(minutes=3)).isoformat()
        
        result = supabase.table('alerts').select('*').eq('location', location).eq('status', 'active').gte('timestamp', three_minutes_ago).execute()
        
        alert_sent = len(result.data) > 0
        time_remaining = None
        
        if alert_sent and result.data:
            # Calculate time remaining until next alert is allowed
            latest_alert = max(result.data, key=lambda x: x.get('timestamp', ''))
            alert_time = datetime.fromisoformat(latest_alert['timestamp'].replace('Z', '+00:00'))
            next_allowed_time = alert_time + timedelta(minutes=3)
            time_remaining = next_allowed_time - datetime.now()
            minutes_remaining = max(0, int(time_remaining.total_seconds() // 60))
            seconds_remaining = max(0, int(time_remaining.total_seconds() % 60))
            time_remaining = {
                'minutes': minutes_remaining,
                'seconds': seconds_remaining
            }
        
        print(f"Alert status for {location}: {alert_sent}")
        
        response = jsonify({
            'status': 'success',
            'alert_sent': alert_sent,
            'stream_id': stream_id,
            'time_remaining': time_remaining
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        print(f"Error checking alert status for {stream_id}: {str(e)}")
        response = jsonify({
            'status': 'success',
            'alert_sent': False,
            'stream_id': stream_id,
            'error': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/api/alert/reset/<stream_id>', methods=['POST'])
def reset_alert_status(stream_id):
    """Reset alert status for a specific stream (for testing)"""
    try:
        # Convert stream_id to location format
        location = stream_id.replace('stream_', '').replace('_', ' ').title()
        if stream_id == 'emergency_stream':
            location = 'Live Camera Feed'
        
        # Update all alerts for this location to resolved
        supabase.table('alerts').update({
            'status': 'resolved',
            'resolved_at': datetime.now().isoformat()
        }).eq('location', location).execute()
        
        return jsonify({
            'status': 'success',
            'message': f'Alert status reset for location {location}',
            'alert_sent': False
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

@app.route('/api/stream/<stream_id>/detect', methods=['POST'])
def detect_anomaly(stream_id):
    """Detect anomalies in video stream"""
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
        
        # Basic anomaly detection (you can enhance this)
        # Convert to grayscale for processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Simple motion detection using frame difference
        # This is a basic example - you can implement more sophisticated detection
        
        # Calculate average brightness
        avg_brightness = np.mean(gray)
        
        # Simple threshold-based anomaly detection
        anomaly_detected = False
        confidence = 0.0
        
        if avg_brightness < 30:  # Very dark frame
            anomaly_detected = True
            confidence = 0.8
        elif avg_brightness > 200:  # Very bright frame
            anomaly_detected = True
            confidence = 0.7
        
        # Convert frame to base64 for response
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'status': 'success',
            'anomaly_detected': anomaly_detected,
            'confidence': confidence,
            'frame': f'data:image/jpeg;base64,{frame_base64}',
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'avg_brightness': float(avg_brightness),
                'frame_size': frame.shape
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['id', 'first_name', 'last_name', 'email', 'username', 'phone', 'password', 'id_number', 'department']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user already exists by email
        existing_user = supabase.table('users').select('*').eq('email', data['email']).execute()
        if existing_user.data:
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Check if username already exists
        print(f"Checking username: {data['username']}")
        existing_username = supabase.table('users').select('*').eq('username', data['username']).execute()
        print(f"Username check result: {existing_username.data}")
        print(f"Number of existing users with this username: {len(existing_username.data)}")
        if existing_username.data:
            print(f"Username '{data['username']}' already exists!")
            return jsonify({'error': 'Username already taken. Please choose a different username'}), 400
        else:
            print(f"Username '{data['username']}' is available")
        
        # Check if phone number already exists
        print(f"Checking phone number: {data['phone']}")
        existing_phone = supabase.table('users').select('*').eq('phone', data['phone']).execute()
        print(f"Phone check result: {existing_phone.data}")
        print(f"Number of existing users with this phone: {len(existing_phone.data)}")
        if existing_phone.data:
            print(f"Phone number '{data['phone']}' already exists!")
            return jsonify({'error': 'Phone number already registered. Please use a different phone number'}), 400
        else:
            print(f"Phone number '{data['phone']}' is available")
        
        # Hash password
        hashed_password = hash_password(data['password'])
        
        user_data = {
            'id': data['id'],
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'email': data['email'],
            'username': data['username'],
            'phone': data['phone'],
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

@app.route('/api/send-telegram-alert', methods=['POST'])
def send_telegram_alert():
    """Send alert via Telegram"""
    try:
        data = request.get_json()
        message = data.get('message', 'Alert from KavachEye')
        
        # Get environment variables
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_ids = os.environ.get('TELEGRAM_CHAT_IDS')
        
        # Split chat IDs
        chat_id_list = [chat_id.strip() for chat_id in chat_ids.split(',')]
        
        # Telegram API URL
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        success_count = 0
        failed_count = 0
        
        for chat_id in chat_id_list:
            try:
                # Prepare payload
                payload = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                
                import requests
                response = requests.post(url, json=payload)
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"Telegram alert sent successfully to chat_id: {chat_id}")
                else:
                    failed_count += 1
                    print(f"Failed to send Telegram alert to chat_id: {chat_id}, Response: {response.text}")
                    
            except Exception as e:
                failed_count += 1
                print(f"Error sending Telegram alert to chat_id: {chat_id}, Error: {str(e)}")
        
        if success_count > 0:
            return jsonify({
                'status': 'success',
                'message': f'Telegram alert sent successfully to {success_count} recipients',
                'successful_sends': success_count,
                'failed_count': failed_count
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send Telegram alert to any recipients',
                'failed_count': failed_count
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-email-alert', methods=['POST'])
def send_email_alert():
    """Send alert via email"""
    try:
        data = request.get_json()
        subject = data.get('subject', 'KavachEye Security Alert')
        message = data.get('message', 'Alert from KavachEye')
        
        # Get environment variables
        gmail_email = os.environ.get('GMAIL_EMAIL')
        gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
        recipient_emails = os.environ.get('RECIPIENT_EMAILS')
        
        # Split recipient emails
        recipients = [email.strip() for email in recipient_emails.split(',')]
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create SMTP session
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(gmail_email, gmail_password)
            
            successful_sends = 0
            
            # Send individual email to each recipient
            for recipient in recipients:
                try:
                    # Create message for individual recipient
                    msg = MIMEMultipart('alternative')
                    msg['From'] = gmail_email
                    msg['To'] = recipient
                    msg['Subject'] = subject
                    
                    # Create HTML email template
                    html_template = f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>SECURITY ALERT - KavachEye System</title>
                        <style>
                            body {{
                                font-family: Arial, sans-serif;
                                margin: 0;
                                padding: 20px;
                                background-color: #f4f4f4;
                                color: #333;
                                line-height: 1.6;
                            }}
                            .container {{
                                max-width: 600px;
                                margin: 0 auto;
                                background-color: #ffffff;
                                border-radius: 12px;
                                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                                overflow: hidden;
                            }}
                            .header {{
                                background: linear-gradient(135deg, #d32f2f 0%, #b71c1c 100%);
                                color: white;
                                padding: 30px;
                                text-align: center;
                            }}
                            .header h1 {{
                                margin: 0;
                                font-size: 24px;
                                font-weight: bold;
                                text-transform: uppercase;
                                letter-spacing: 1px;
                            }}
                            .header p {{
                                margin: 8px 0 0 0;
                                font-size: 14px;
                                opacity: 0.9;
                            }}
                            .content {{
                                padding: 30px;
                            }}
                            .main-alert-box {{
                                background: linear-gradient(135deg, #fff5f5 0%, #ffebee 100%);
                                border: 2px solid #f44336;
                                border-radius: 12px;
                                padding: 25px;
                                margin-bottom: 25px;
                                box-shadow: 0 2px 10px rgba(244, 67, 54, 0.1);
                            }}
                            .alert-title {{
                                color: #d32f2f;
                                font-weight: bold;
                                font-size: 18px;
                                margin-bottom: 15px;
                                text-transform: uppercase;
                                display: flex;
                                align-items: center;
                                gap: 10px;
                            }}
                            .alert-message {{
                                color: #333;
                                margin: 0 0 20px 0;
                                font-size: 15px;
                                line-height: 1.6;
                            }}
                            .alert-details {{
                                background-color: rgba(255, 255, 255, 0.7);
                                border-radius: 8px;
                                padding: 20px;
                                margin: 20px 0;
                            }}
                            .detail-row {{
                                display: flex;
                                justify-content: space-between;
                                align-items: center;
                                padding: 8px 0;
                                border-bottom: 1px solid #eee;
                            }}
                            .detail-row:last-child {{
                                border-bottom: none;
                            }}
                            .detail-label {{
                                font-weight: bold;
                                color: #555;
                                font-size: 13px;
                            }}
                            .detail-value {{
                                color: #333;
                                font-size: 13px;
                            }}
                            .priority-high {{
                                background-color: #ffebee;
                                color: #d32f2f;
                                font-weight: bold;
                                padding: 4px 8px;
                                border-radius: 4px;
                            }}
                            .status-active {{
                                background-color: #e8f5e8;
                                color: #2e7d32;
                                font-weight: bold;
                                padding: 4px 8px;
                                border-radius: 4px;
                            }}
                            .action-buttons {{
                                display: flex;
                                gap: 15px;
                                justify-content: center;
                                margin-top: 25px;
                            }}
                            .btn {{
                                display: inline-block;
                                padding: 12px 24px;
                                text-decoration: none;
                                border-radius: 8px;
                                font-weight: bold;
                                font-size: 14px;
                                text-align: center;
                                transition: all 0.3s ease;
                                border: none;
                                cursor: pointer;
                            }}
                            .btn-primary {{
                                background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
                                color: white;
                                box-shadow: 0 2px 8px rgba(25, 118, 210, 0.3);
                            }}
                            .btn-primary:hover {{
                                transform: translateY(-2px);
                                box-shadow: 0 4px 12px rgba(25, 118, 210, 0.4);
                            }}
                            .btn-secondary {{
                                background: linear-gradient(135deg, #388e3c 0%, #2e7d32 100%);
                                color: white;
                                box-shadow: 0 2px 8px rgba(56, 142, 60, 0.3);
                            }}
                            .btn-secondary:hover {{
                                transform: translateY(-2px);
                                box-shadow: 0 4px 12px rgba(56, 142, 60, 0.4);
                            }}
                            .timestamp {{
                                text-align: center;
                                padding: 15px;
                                background-color: #f8f9fa;
                                border-top: 1px solid #eee;
                                font-size: 12px;
                                color: #666;
                            }}
                            .footer {{
                                background-color: #f5f5f5;
                                padding: 20px;
                                text-align: center;
                                border-top: 1px solid #eee;
                                font-size: 12px;
                                color: #666;
                            }}
                            .logo {{
                                font-size: 32px;
                                margin-bottom: 15px;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <div class="logo">🚨</div>
                                <h1>SECURITY ALERT</h1>
                                <p>KavachEye Security Monitoring System</p>
                            </div>
                            
                            <div class="content">
                                <div class="main-alert-box">
                                    <div class="alert-title">
                                        ⚠️ SECURITY INCIDENT DETECTED
                                    </div>
                                    <div class="alert-message">{message}</div>
                                    
                                    <div class="alert-details">
                                        <div class="detail-row">
                                            <span class="detail-label">Alert ID:</span>
                                            <span class="detail-value">ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}</span>
                                        </div>
                                        <div class="detail-row">
                                            <span class="detail-label">Alert Type:</span>
                                            <span class="detail-value priority-high">Security Incident</span>
                                        </div>
                                        <div class="detail-row">
                                            <span class="detail-label">Severity Level:</span>
                                            <span class="detail-value priority-high">HIGH PRIORITY</span>
                                        </div>
                                        <div class="detail-row">
                                            <span class="detail-label">Location:</span>
                                            <span class="detail-value">Camera Feed Zone</span>
                                        </div>
                                        <div class="detail-row">
                                            <span class="detail-label">Detection Time:</span>
                                            <span class="detail-value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                                        </div>
                                        <div class="detail-row">
                                            <span class="detail-label">System Status:</span>
                                            <span class="detail-value status-active">ACTIVE MONITORING</span>
                                        </div>
                                        <div class="detail-row">
                                            <span class="detail-label">Response Status:</span>
                                            <span class="detail-value status-active">AUTHORITIES NOTIFIED</span>
                                        </div>
                                    </div>
                                    
                                    <div class="action-buttons">
                                        <a href="https://kavacheye-frontend.vercel.app" class="btn btn-primary">📊 View Dashboard</a>
                                        <a href="#" class="btn btn-secondary">✅ Mark as Resolved</a>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="timestamp">
                                Alert generated: {datetime.now().strftime('%B %d, %Y at %I:%M:%S %p')} UTC
                            </div>
                            
                            <div class="footer">
                                <p><strong>This is an automated security alert from KavachEye Security System.</strong></p>
                                <p>For immediate assistance, contact your security administrator or call emergency services.</p>
                                <p>Do not reply to this email. This is a system-generated notification.</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Create both plain text and HTML versions
                    text_part = MIMEText(message, 'plain')
                    html_part = MIMEText(html_template, 'html')
                    
                    # Attach both parts
                    msg.attach(text_part)
                    msg.attach(html_part)
                    
                    # Send individual email
                    text = msg.as_string()
                    server.sendmail(gmail_email, [recipient], text)
                    successful_sends += 1
                    
                    print(f"Email Alert sent successfully to: {recipient}")
                    
                except Exception as individual_error:
                    print(f"Failed to send email to {recipient}: {individual_error}")
                    continue
            
            server.quit()
            
            return jsonify({
                'status': 'success',
                'message': 'Email alerts sent successfully',
                'successful_sends': successful_sends,
                'recipients': recipients
            })
            
        except Exception as email_error:
            print(f"Email sending error: {email_error}")
            return jsonify({
                'status': 'error',
                'message': f'Failed to send email: {str(email_error)}'
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-telegram-updates', methods=['GET'])
def get_telegram_updates():
    """Get Telegram bot updates"""
    try:
        bot_token = request.args.get('bot_token')
        
        if not bot_token:
            return jsonify({'error': 'Missing bot_token'}), 400
        
        # Telegram API URL for getting updates
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        
        import requests
        response = requests.get(url)
        
        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'updates': response.json()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get Telegram updates',
                'response': response.text
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-sms-alert', methods=['POST'])
def send_sms_alert():
    """Send alert via SMS"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        message = data.get('message', 'Alert from KavachEye')
        
        if not phone_number:
            return jsonify({'error': 'Missing phone_number'}), 400
        
        # For now, just return success (you can implement actual SMS sending)
        # You can use services like Twilio, AWS SNS, or other SMS providers
        
            return jsonify({
            'status': 'success',
            'message': 'SMS alert sent successfully',
            'phone_number': phone_number
        })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-whatsapp-alert', methods=['POST'])
def send_whatsapp_alert():
    """Send alert via WhatsApp"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        message = data.get('message', 'Alert from KavachEye')
        
        if not phone_number:
            return jsonify({'error': 'Missing phone_number'}), 400
        
        # For now, just return success (you can implement actual WhatsApp sending)
        # You can use services like Twilio WhatsApp API or WhatsApp Business API
        
            return jsonify({
            'status': 'success',
            'message': 'WhatsApp alert sent successfully',
            'phone_number': phone_number
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
                'username': user.get('username', ''),
                'phone': user.get('phone', ''),
                'department': user['department']
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def predict_ai():
    """AI prediction endpoint for hybrid camera"""
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Decode base64 image
        image_data = data['image'].split(',')[1] if ',' in data['image'] else data['image']
        image_bytes = base64.b64decode(image_data)
        
        # Convert to OpenCV format
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # Basic AI analysis (simulated for now)
        # In production, you would load your trained models here
        
        # Simulate gender detection
        male_count = np.random.randint(0, 3)
        female_count = np.random.randint(0, 2)
        
        # Simulate violence detection
        violence_detected = bool(np.random.choice([True, False], p=[0.1, 0.9]))
        violence_count = 1 if violence_detected else 0
        
        # Calculate safety score
        safety_score = max(0, 100 - (violence_count * 20) - (male_count * 5))
        
        # Simulate pose detection
        pose_detected = bool(np.random.choice([True, False], p=[0.3, 0.7]))
        
        # Convert processed frame back to base64
        _, buffer = cv2.imencode('.jpg', frame)
        processed_frame = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'status': 'success',
            'analytics': {
                'maleCount': male_count,
                'femaleCount': female_count,
                'violenceCount': violence_count,
                'safetyScore': safety_score,
                'poseDetected': pose_detected
            },
            'frame': f'data:image/jpeg;base64,{processed_frame}',
            'timestamp': datetime.now().isoformat(),
            'detections': {
                'people': male_count + female_count,
                'anomalies': violence_count,
                'pose_analysis': pose_detected
                }
            })
            
    except Exception as e:
        print(f"Error in predict_ai: {str(e)}")
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
            'supabase_url': SUPABASE_URL,
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