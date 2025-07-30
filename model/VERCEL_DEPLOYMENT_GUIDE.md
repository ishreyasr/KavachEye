# Vercel Deployment Guide for KavachEye AI Model Service

## 🚀 **Deploy Your AI Model Service to Vercel**

### **What's Different from the Original**

The original `combined.py` uses **Flask-SocketIO** for real-time WebSocket communication, which Vercel doesn't support well. This Vercel version:

✅ **Removes WebSocket functionality** (not supported on Vercel)  
✅ **Converts to REST API** (fully supported)  
✅ **Keeps all AI models** (YOLO, Gender, Violence, Face Detection)  
✅ **Processes frames via HTTP POST** (instead of real-time streaming)  
✅ **Returns JSON results** (instead of WebSocket events)  

## 📋 **Step-by-Step Deployment**

### **Step 1: Prepare Your Repository**

1. **Ensure your model folder structure is correct:**
   ```
   model/
   ├── app_vercel.py              # Vercel-compatible Flask app
   ├── requirements-vercel.txt     # Vercel-specific requirements
   ├── vercel.json                # Vercel configuration
   ├── yolov8n-pose.pt           # YOLO model
   ├── gender_model_best.h5      # Gender detection model
   ├── violence.h5               # Violence detection model
   ├── emotion_model.h5          # Emotion detection model
   ├── deploy.prototxt.txt       # Face detection config
   ├── res10_300x300_ssd_iter_140000.caffemodel  # Face detection model
   ├── labels_gender.txt         # Gender labels
   ├── labels_violence.txt       # Violence labels
   └── README.md                 # Documentation
   ```

2. **Commit and push to GitHub:**
   ```bash
   git add .
   git commit -m "Add Vercel-compatible AI model service"
   git push origin main
   ```

### **Step 2: Create Vercel Project**

1. **Go to [vercel.com](https://vercel.com)**
2. **Sign up** with your GitHub account
3. **Import your repository**
4. **Set Root Directory** to `model`
5. **Configure Build Settings:**
   ```
   Framework Preset: Other
   Root Directory: model
   Build Command: pip install -r requirements-vercel.txt
   Output Directory: .
   Install Command: pip install -r requirements-vercel.txt
   ```

### **Step 3: Deploy**

1. **Click "Deploy"** in Vercel dashboard
2. **Wait for build** to complete (may take 5-10 minutes due to large models)
3. **Get your deployment URL** (e.g., `https://kavacheye-ai-models.vercel.app`)

## 🎯 **API Endpoints**

### **1. Health Check**
```bash
GET https://your-model-service.vercel.app/
```

Response:
```json
{
  "message": "KavachEye AI Model Service (Vercel)",
  "status": "running",
  "models_loaded": true,
  "endpoints": {
    "/": "Health check",
    "/predict": "Process frame for AI analysis",
    "/status": "Model status"
  }
}
```

### **2. Model Status**
```bash
GET https://your-model-service.vercel.app/status
```

Response:
```json
{
  "models_loaded": true,
  "models": {
    "yolo_model": true,
    "gender_model": true,
    "violence_model": true,
    "face_net": true
  },
  "timestamp": 1640995200.0
}
```

### **3. Process Frame (Main Endpoint)**
```bash
POST https://your-model-service.vercel.app/predict
Content-Type: application/json

{
  "frame": "base64_encoded_image_data"
}
```

Response:
```json
{
  "status": "success",
  "results": {
    "pose_detection": {
      "detected": true,
      "keypoints_count": 17,
      "confidence": 0.85
    },
    "gender_detection": {
      "detected": true,
      "gender": "Female",
      "confidence": 0.92
    },
    "violence_detection": {
      "detected": true,
      "classification": "Non-violent",
      "confidence": 0.78
    },
    "face_detection": {
      "detected": true,
      "faces_count": 1,
      "faces": [
        {
          "confidence": 0.95,
          "box": [100, 150, 200, 250]
        }
      ]
    },
    "timestamp": 1640995200.0
  }
}
```

## 🔧 **How to Use from Frontend**

### **JavaScript Example:**
```javascript
// Capture frame from camera
const canvas = document.createElement('canvas');
const context = canvas.getContext('2d');
canvas.width = video.videoWidth;
canvas.height = video.videoHeight;
context.drawImage(video, 0, 0);

// Convert to base64
const frameData = canvas.toDataURL('image/jpeg', 0.8);

// Send to AI service
fetch('https://your-model-service.vercel.app/predict', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    frame: frameData
  })
})
.then(response => response.json())
.then(data => {
  console.log('AI Analysis:', data.results);
  
  // Handle results
  if (data.results.violence_detection.detected) {
    console.log('Violence detected:', data.results.violence_detection.classification);
  }
  
  if (data.results.pose_detection.detected) {
    console.log('Pose detected with confidence:', data.results.pose_detection.confidence);
  }
});
```

## ⚠️ **Important Limitations**

### **1. No Real-time Streaming**
- ❌ **WebSocket connections** not supported
- ✅ **HTTP POST requests** for frame processing
- ✅ **Batch processing** of individual frames

### **2. Function Timeouts**
- ⚠️ **60-second timeout** (increased from default 30s)
- ⚠️ **Large model loading** may take time
- ✅ **Cold start optimization** for subsequent requests

### **3. Model Size**
- ⚠️ **Large model files** (YOLO, TensorFlow models)
- ⚠️ **Deployment time** may be longer
- ✅ **Once loaded, fast inference**

## 🎯 **Testing Your Deployment**

### **1. Health Check**
```bash
curl https://your-model-service.vercel.app/
```

### **2. Test with Sample Image**
```bash
# Convert image to base64
base64 -i sample.jpg | tr -d '\n' > image.txt

# Send to API
curl -X POST https://your-model-service.vercel.app/predict \
  -H "Content-Type: application/json" \
  -d '{
    "frame": "'$(cat image.txt)'"
  }'
```

## 🚀 **Complete KavachEye Stack**

```
Frontend:     Vercel (KavachEye-frontend)     ✅ Ready
Backend API:  Vercel (KavachEye-backend)      ✅ LIVE
AI Models:    Vercel (KavachEye-ai-models)    ✅ Ready
Database:     Supabase (PostgreSQL)            ✅ Connected
```

## 🛡️ **Security & Performance**

### **✅ Benefits:**
- **HTTPS encryption** for all communications
- **Global CDN** for fast response times
- **Automatic scaling** for traffic spikes
- **No server management** required

### **⚠️ Considerations:**
- **Model loading time** on cold starts
- **Function timeout limits** for long processing
- **No persistent WebSocket connections**

## 🎯 **Next Steps**

1. **Deploy the model service** to Vercel
2. **Test the API endpoints** with sample images
3. **Update your frontend** to use the new AI service
4. **Integrate with your main backend** for complete workflow

Your KavachEye AI model service is now ready for Vercel deployment! 🚀