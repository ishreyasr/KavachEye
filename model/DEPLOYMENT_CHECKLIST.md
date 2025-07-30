# Render Deployment Checklist

## ✅ Pre-Deployment Checklist

### Repository Setup
- [ ] Code is pushed to GitHub repository
- [ ] All model files are in the `model/` directory
- [ ] `requirements.txt` is up to date
- [ ] `runtime.txt` specifies Python 3.11.0
- [ ] `build.sh` and `start.sh` are executable
- [ ] Application works locally (`python combined.py`)

### Required Files in `model/` Directory
- [ ] `combined.py` (main application)
- [ ] `requirements.txt` (dependencies)
- [ ] `runtime.txt` (Python version)
- [ ] `build.sh` (build script)
- [ ] `start.sh` (start script)
- [ ] `yolov8n-pose.pt` (YOLO model)
- [ ] `gender_model_best.h5` (gender model)
- [ ] `violence.h5` (violence model)
- [ ] `deploy.prototxt.txt` (face detection)
- [ ] `res10_300x300_ssd_iter_140000.caffemodel` (face detection)
- [ ] `labels_violence.txt` (labels)

## ✅ Render Setup Checklist

### Account Setup
- [ ] Render account created
- [ ] GitHub account connected
- [ ] Email verified

### Service Configuration
- [ ] New Web Service created
- [ ] GitHub repository connected
- [ ] Root Directory set to `model`
- [ ] Build Command: `chmod +x build.sh && ./build.sh`
- [ ] Start Command: `chmod +x start.sh && ./start.sh`
- [ ] Environment: Python 3
- [ ] Auto-Deploy enabled
- [ ] Health Check Path: `/health`

### Environment Variables (Optional)
- [ ] `RENDER=true`
- [ ] `PYTHONPATH=/opt/render/project/src`

## ✅ Post-Deployment Checklist

### Testing
- [ ] Build completed successfully
- [ ] Service is running (green status)
- [ ] Health check passes: `/health`
- [ ] Test endpoint works: `/test`
- [ ] Status endpoint works: `/status`
- [ ] WebSocket connection works (if applicable)

### Monitoring
- [ ] Logs are accessible
- [ ] No error messages in logs
- [ ] Service responds within reasonable time
- [ ] Memory usage is within limits (512MB)

## ✅ Troubleshooting Checklist

### If Build Fails
- [ ] Check build logs for specific errors
- [ ] Verify all files are in correct location
- [ ] Ensure `requirements.txt` is valid
- [ ] Check if model files are too large (use Git LFS)

### If Service Won't Start
- [ ] Check start logs
- [ ] Verify `start.sh` has execute permissions
- [ ] Ensure `combined.py` exists and is valid
- [ ] Check if PORT environment variable is set

### If Models Don't Load
- [ ] Check if models are in correct location
- [ ] Verify model files are not corrupted
- [ ] Check memory usage (free tier limit: 512MB)
- [ ] Test with smaller models if needed

## ✅ Performance Optimization

### Free Tier Limits
- [ ] Memory usage < 512MB
- [ ] Storage usage < 1GB
- [ ] Bandwidth usage < 750GB/month
- [ ] Build time < 500 minutes/month

### Optimization Tips
- [ ] Use smaller model files if possible
- [ ] Implement lazy loading for models
- [ ] Optimize image processing
- [ ] Use efficient data structures

## ✅ Security Checklist

- [ ] No sensitive data in code
- [ ] Environment variables used for secrets
- [ ] HTTPS enabled (automatic on Render)
- [ ] CORS properly configured
- [ ] Input validation implemented

## ✅ Documentation

- [ ] README updated with deployment info
- [ ] API documentation available
- [ ] Environment variables documented
- [ ] Troubleshooting guide created

---

## Quick Commands

### Local Testing
```bash
cd model
python combined.py
```

### Check Files
```bash
ls -la model/
```

### Test Endpoints
```bash
curl https://your-service.onrender.com/health
curl https://your-service.onrender.com/test
curl https://your-service.onrender.com/status
```

### View Logs (on Render Dashboard)
- Go to your service
- Click "Logs" tab
- Check for errors

---

**Deployment Status: [ ] Ready [ ] In Progress [ ] Complete**