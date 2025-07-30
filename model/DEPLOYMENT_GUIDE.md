# KavachEye Model Service Deployment Guide

## 🚀 Deployment Options

### Option 1: Docker Desktop (Recommended - FREE)

#### Prerequisites:
- Docker Desktop installed
- Git repository cloned

#### Steps:
1. **Navigate to model directory:**
   ```bash
   cd model
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

3. **Access the service:**
   - Local: http://localhost:5001
   - Network: http://your-ip:5001

#### Benefits:
- ✅ Completely FREE
- ✅ Easy to manage
- ✅ Consistent environment
- ✅ No port conflicts
- ✅ Easy scaling

### Option 2: Render.com (Cloud Deployment)

#### Steps:
1. **Create new Web Service on Render**
2. **Connect your GitHub repository**
3. **Configure build settings:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python combined.py`
4. **Set environment variables:**
   - `PORT`: 5001 (or let Render assign)
5. **Deploy!**

### Option 3: Railway.app (Alternative Cloud)

#### Steps:
1. **Sign up at railway.app**
2. **Connect GitHub repository**
3. **Deploy automatically**
4. **Get public URL**

## 🔧 Configuration

### Environment Variables:
```bash
PORT=5001
PYTHONPATH=/app
```

### Required Files:
- ✅ `combined.py` - Main application
- ✅ `requirements.txt` - Dependencies
- ✅ `Dockerfile` - Container configuration
- ✅ `docker-compose.yml` - Local deployment
- ✅ `Procfile` - Cloud deployment
- ✅ `runtime.txt` - Python version

## 🐳 Docker Commands

### Build Image:
```bash
docker build -t kavacheye-model .
```

### Run Container:
```bash
docker run -p 5001:5001 kavacheye-model
```

### Stop Container:
```bash
docker stop $(docker ps -q --filter ancestor=kavacheye-model)
```

## 🔍 Troubleshooting

### Port Issues:
- **Problem**: "No open ports" error
- **Solution**: Use Docker or ensure port 5001 is available

### Memory Issues:
- **Problem**: Model loading fails
- **Solution**: Increase Docker memory limit to 4GB+

### Dependencies:
- **Problem**: Missing packages
- **Solution**: Check `requirements.txt` is complete

## 📊 Monitoring

### Health Check:
```bash
curl http://localhost:5001/
```

### Logs:
```bash
docker-compose logs -f
```

## 🚀 Quick Start (Docker Desktop)

1. **Open Docker Desktop**
2. **Open terminal in model directory**
3. **Run:**
   ```bash
   docker-compose up --build
   ```
4. **Access:** http://localhost:5001
5. **Test:** Open frontend and connect to port 5001

## 💡 Tips

- **Use Docker Desktop** for easiest deployment
- **Monitor logs** for debugging
- **Test locally** before cloud deployment
- **Use environment variables** for configuration 