# KavachEye Backend

## 🛡️ Women Safety Platform Backend

This is the backend API for the KavachEye women safety platform, deployed on Vercel with Supabase database.

## 🚀 Deployment

- **Platform:** Vercel
- **Database:** Supabase (PostgreSQL)
- **Framework:** Flask
- **Status:** Ready for deployment

## 📋 API Endpoints

### Health Check
```
GET /api/health
```

### User Management
```
POST /api/register
POST /api/login
```

### Stream Management
```
POST /api/streams/start
GET /api/streams/frame
POST /api/streams/stop
GET /api/streams/list
```

### Alert Management
```
POST /api/alerts/create
GET /api/alerts/list
PUT /api/alerts/resolve
```

## 🔧 Environment Variables

Required environment variables in Vercel:

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here
JWT_SECRET=your-jwt-secret-here
```

## 🎯 Quick Test

```bash
# Health check
curl https://kavacheyebackend.vercel.app/api/health

# Register user
curl -X POST https://kavacheyebackend.vercel.app/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "id": "user123",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "password": "password123",
    "id_number": "EMP001",
    "department": "Security"
  }'
```

## 🛡️ KavachEye - A Better Tomorrow for Women 