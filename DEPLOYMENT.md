# 🚀 Deployment Guide for Adaptive SRS Language App

## Overview
This guide will help you deploy your Adaptive SRS app to production using:
- **Frontend**: Vercel (free)
- **Backend**: Railway (free tier)
- **Database**: Neon PostgreSQL (already set up)

## 📋 Prerequisites
- GitHub account
- Vercel account (free)
- Railway account (free)
- Your Neon database connection string

## 🔧 Step 1: Push to GitHub

1. Create a new repository on GitHub
2. Push your code:
```bash
git init
git add .
git commit -m "Initial commit - Adaptive SRS App"
git branch -M main
git remote add origin https://github.com/yourusername/adaptive-srs-app.git
git push -u origin main
```

## 🌐 Step 2: Deploy Backend to Railway

1. Go to [railway.app](https://railway.app)
2. Sign up/login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect it's a Python app

### Environment Variables for Railway:
Set these in Railway dashboard:
```
DATABASE_URL=postgresql://neondb_owner:npg_PCbMHtoXv02q@ep-muddy-mode-a77zmnnd-pooler.ap-southeast-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
POSTGRES_HOST=ep-muddy-mode-a77zmnnd-pooler.ap-southeast-2.aws.neon.tech
POSTGRES_PORT=5432
POSTGRES_DB=neondb
POSTGRES_USER=neondb_owner
POSTGRES_PASSWORD=npg_PCbMHtoXv02q
```

## 🎨 Step 3: Deploy Frontend to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Sign up/login with GitHub
3. Click "New Project"
4. Import your GitHub repository
5. Vercel will auto-detect it's a Next.js app
6. Set the root directory to `apps/web`

### Environment Variables for Vercel:
Set this in Vercel dashboard:
```
NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app
```
(Replace with your actual Railway URL after deployment)

## 🔗 Step 4: Update CORS

After getting your Vercel URL, update the CORS settings in `api/main.py`:
```python
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://your-vercel-app.vercel.app",  # Add your actual URL
]
```

## ✅ Step 5: Test Production

1. Visit your Vercel URL
2. Test card loading and reviews
3. Verify data is saved to your Neon database

## 🎯 Your Production URLs
- **Frontend**: `https://your-app.vercel.app`
- **Backend API**: `https://your-app.railway.app`
- **API Docs**: `https://your-app.railway.app/docs`

## 🔧 Troubleshooting

### Common Issues:
1. **CORS errors**: Update allowed_origins in main.py
2. **Database connection**: Verify environment variables
3. **Build failures**: Check requirements.txt and package.json

### Logs:
- **Railway**: Check deployment logs in Railway dashboard
- **Vercel**: Check function logs in Vercel dashboard

## 🎉 Success!
Your Adaptive SRS Language Learning App is now live and accessible worldwide!
