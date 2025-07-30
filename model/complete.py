from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS
import time
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from keras.layers import DepthwiseConv2D
from ultralytics import YOLO
from twilio.rest import Client
import base64
import threading
# Import show.py methods
from show import run_show

# Twilio credentials
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
emergency_contact = os.getenv('EMERGENCY_CONTACT')

# Initialize Twilio client if credentials are available
if account_sid and auth_token:
    client = Client(account_sid, auth_token)
    print("Twilio client initialized successfully")
else:
    client = None
    print("WARNING: Twilio credentials not found. SMS/call features will be disabled.")

# Flask and SocketIO setup
app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://localhost:5000', '*'])  # Enable CORS for frontend and KavachEye
socketio = SocketIO(app, cors_allowed_origins=['http://localhost:3000', 'http://localhost:5000', '*'])

# Twilio SOS functions
def send_sos_alert(authority_number, message):
    if client is None:
        print(f"[MOCK] SMS would be sent to {authority_number}: {message}")
        return
    
    try:
        client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=authority_number
        )
        print(f"SMS sent to {authority_number}")
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")

def make_sos_call(authority_number, twiml_url):
    if client is None:
        print(f"[MOCK] Call would be initiated to {authority_number}")
        return
    
    try:
        call = client.calls.create(
            to=authority_number,
            from_=twilio_phone_number,
            url=twiml_url  # TwiML URL containing instructions for the call
        )
        print(f"Call initiated to {authority_number}, Call SID: {call.sid}")
    except Exception as e:
        print(f"Error making call: {str(e)}")

def start_sos_sequence(authority_number, message, twiml_url):
    alert_count = 0
    max_alerts = 15
    call_after_alerts = 2
    while alert_count < max_alerts:
        send_sos_alert(authority_number, message)
        alert_count += 1
        if alert_count == call_after_alerts:
            make_sos_call(authority_number, twiml_url)
        if alert_count < max_alerts:
            time.sleep(30)

# Load model with custom objects
class CustomDepthwiseConv2D(DepthwiseConv2D):
    def __init__(self, *args, **kwargs):
        if 'groups' in kwargs:
            kwargs.pop('groups')
        super(CustomDepthwiseConv2D, self).__init__(*args, **kwargs)

# Get the directory of the current script
import os
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load models for gender, emotion, and violence detection with correct paths
gender_model = load_model(os.path.join(current_dir, 'gender_model_best.h5'))
emotion_model = load_model(os.path.join(current_dir, 'emotion_model.h5'))
violence_model = load_model(os.path.join(current_dir, "violence.h5"), custom_objects={'DepthwiseConv2D': CustomDepthwiseConv2D}, compile=False)
pose_model = YOLO(os.path.join(current_dir, "yolov8n-pose.pt"))

# Define labels and confidence threshold for gender detection
gender_labels = ['Male', 'Female']
confidence_threshold = 0.6

# Load SSD model files for face detection
ssd_prototxt = os.path.join(current_dir, 'deploy.prototxt.txt')
ssd_weights = os.path.join(current_dir, 'res10_300x300_ssd_iter_140000.caffemodel')
face_net = cv2.dnn.readNetFromCaffe(ssd_prototxt, ssd_weights)

# Emotion labels
emotions = ["positive", "negative", "neutral"]

# Violence detection labels
violence_labels = open(os.path.join(current_dir, "labels_violence.txt"), "r").readlines()

# Initialize webcam
cap = cv2.VideoCapture(0)

# Global counters for male, female, frames, and violence detection
male_count = 0
female_count = 0
frame_count = 0
violence_count = 0
ratio = 0.0
start_time = time.time()

# Function to preprocess face for gender detection
def preprocess_face(face, img_size=(150, 150)):
    face = cv2.resize(face, img_size)
    face = face.astype('float32') / 255.0
    face = np.expand_dims(face, axis=0)
    return face

# Function to handle gender, emotion, and violence detection
def detect_face(frame):
    global male_count, female_count, frame_count, violence_count, start_time
    global ratio
    
    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    face_net.setInput(blob)
    detections = face_net.forward()
    
    frame_male_count = 0
    frame_female_count = 0
    
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            face = frame[startY:endY, startX:endX]
            
            # Gender detection
            face_preprocessed = preprocess_face(face)
            gender_prediction = gender_model.predict(face_preprocessed)
            predicted_gender_prob = gender_prediction[0][0]
            
            if predicted_gender_prob > (1 - confidence_threshold):
                gender = 'Female'
                frame_female_count += 1
            elif predicted_gender_prob < confidence_threshold:
                gender = 'Male'
                frame_male_count += 1
            else:
                gender = 'Neutral'
            
            # Emotion detection
            roi_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
            roi_gray = cv2.resize(roi_gray, (48, 48))
            roi_gray = roi_gray.astype('float') / 255.0
            roi_gray = img_to_array(roi_gray)
            roi_gray = np.expand_dims(roi_gray, axis=0)
            emotion_prediction = emotion_model.predict(roi_gray)
            max_index = np.argmax(emotion_prediction[0])
            emotion = emotions[max_index]
            
            # Violence detection
            image_resized = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
            image_array = np.asarray(image_resized, dtype=np.float32).reshape(1, 224, 224, 3)
            image_array = (image_array / 127.5) - 1
            violence_prediction = violence_model.predict(image_array)
            violence_index = np.argmax(violence_prediction)
            violence_class = violence_labels[violence_index].strip()[2:]
            
            if violence_class == 'violence':
                violence_count += 1
                print(f"Class: {violence_class} | Confidence Score: {str(np.round(violence_prediction[0][violence_index] * 100))[:-2]}%, Count: {violence_count}")
            
            # Draw bounding box and labels
            cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
            cv2.putText(frame, f"{gender}, {emotion}", (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
    
    male_count += frame_male_count
    female_count += frame_female_count
    frame_count += 1
    
    current_time = time.time()
    if current_time - start_time >= 1:
        avg_male = male_count / frame_count
        avg_female = female_count / frame_count
        if avg_female > 0:
            ratio = avg_male / avg_female
        else:
            ratio = 0
        male_count = 0
        female_count = 0
        frame_count = 0
        start_time = current_time
    
    return frame

# Function to handle pose detection using YOLO
def detect_pose(frame):
    results = pose_model(frame)
    plotted_frame = results[0].plot()
    return plotted_frame

# Women Safety Prediction Function
def predict_women_safety(location, time):
    """
    Predict women safety level based on location and time
    This is a mock implementation - in production, this would use:
    - Historical crime data
    - Current surveillance analytics
    - Time-based risk patterns
    - Location-specific safety metrics
    """
    import datetime
    
    # Parse time if it's a string
    if isinstance(time, str):
        try:
            time_obj = datetime.datetime.fromisoformat(time.replace('Z', '+00:00'))
            hour = time_obj.hour
        except:
            hour = datetime.datetime.now().hour
    else:
        hour = datetime.datetime.now().hour
    
    # Mock safety prediction logic
    safety_score = 0.8  # Base safety score
    
    # Time-based risk factors
    if 22 <= hour or hour <= 5:  # Night time (10 PM to 5 AM)
        safety_score -= 0.3
    elif 18 <= hour <= 21:  # Evening (6 PM to 9 PM)
        safety_score -= 0.1
    
    # Location-based risk factors (mock data)
    high_risk_areas = ['downtown', 'industrial', 'isolated', 'parking']
    medium_risk_areas = ['residential', 'suburban']
    
    location_lower = location.lower()
    
    if any(area in location_lower for area in high_risk_areas):
        safety_score -= 0.2
    elif any(area in location_lower for area in medium_risk_areas):
        safety_score -= 0.1
    
    # Use current violence detection data if available
    global violence_count, ratio
    if violence_count > 10:
        safety_score -= 0.3
    elif violence_count > 5:
        safety_score -= 0.1
    
    # Gender ratio consideration (more males might indicate higher risk)
    if ratio > 3:  # Much more males than females
        safety_score -= 0.1
    
    # Ensure safety_score is between 0 and 1
    safety_score = max(0.0, min(1.0, safety_score))
    
    # Determine safety level
    if safety_score >= 0.7:
        safety_level = "safe"
    elif safety_score >= 0.4:
        safety_level = "moderate"
    else:
        safety_level = "unsafe"
    
    return {
        "safety_level": safety_level,
        "safety_score": round(safety_score, 2),
        "risk_factors": {
            "time_risk": "high" if (22 <= hour or hour <= 5) else "low",
            "location_risk": "high" if any(area in location_lower for area in high_risk_areas) else "low",
            "current_violence": violence_count,
            "gender_ratio": round(ratio, 2)
        },
        "recommendations": get_safety_recommendations(safety_level, hour, location_lower)
    }

def get_safety_recommendations(safety_level, hour, location):
    """Generate safety recommendations based on the safety level"""
    recommendations = []
    
    if safety_level == "unsafe":
        recommendations.extend([
            "Avoid this area if possible",
            "Travel in groups",
            "Stay in well-lit areas",
            "Keep emergency contacts ready",
            "Consider alternative routes"
        ])
    elif safety_level == "moderate":
        recommendations.extend([
            "Stay alert and aware of surroundings",
            "Avoid isolated areas",
            "Keep phone charged and accessible"
        ])
    else:
        recommendations.extend([
            "General safety precautions apply",
            "Stay aware of your surroundings"
        ])
    
    # Time-specific recommendations
    if 22 <= hour or hour <= 5:
        recommendations.append("Avoid traveling alone at night")
        recommendations.append("Use well-lit main roads")
    
    return recommendations

# Generate frames for streaming
def generate_frames():
    global violence_count
    while True:
        success, frame = cap.read()
        if not success:
            break
        
        frame = detect_face(frame)
        frame = detect_pose(frame)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        if violence_count > 25:
            print("Threshold for violence crossed")
            # Trigger SOS sequence
            if emergency_contact:
                threading.Thread(target=start_sos_sequence, args=(emergency_contact, 'EMERGENCY ALERT: Violence detected in surveillance feed. Please respond immediately.', 'http://demo.twilio.com/docs/voice.xml')).start()
            else:
                print("WARNING: No emergency contact number provided. Cannot send SOS alert.")
            violence_count = 0

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_averages')
def get_averages():
    global male_count, female_count, frame_count, ratio
    if frame_count > 0:
        avg_male = male_count / frame_count
        avg_female = female_count / frame_count
        if avg_female > 0:
            ratio = avg_male / avg_female
        else:
            ratio = 0
    else:
        avg_male = avg_female = 0
    return jsonify({'avg_male': avg_male, 'avg_female': avg_female, 'ratio': ratio})

@app.route('/predict', methods=['POST'])
def predict_safety():
    """
    Predict women safety level based on location and time
    Expected JSON input: {"location": "downtown", "time": "2024-01-15T22:30:00"}
    Returns: {"safety_level": "safe/moderate/unsafe", ...}
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract location and time from request
        location = data.get('location')
        time_input = data.get('time')
        
        if not location:
            return jsonify({"error": "Location field is required"}), 400
        
        if not time_input:
            return jsonify({"error": "Time field is required"}), 400
        
        # Call the prediction function
        prediction_result = predict_women_safety(location, time_input)
        
        return jsonify(prediction_result), 200
        
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

@socketio.on('connect')
def handle_connect():
    socketio.start_background_task(generate_frames)
    # Start the clustering and mapping task
    socketio.start_background_task(run_show)

if __name__ == '__main__':
    socketio.run(app, debug=True)