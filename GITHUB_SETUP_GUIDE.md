# 📁 GitHub Setup Guide for Railway Deployment

## 🔧 **Step 1: Create GitHub Repository**

### **1. Go to GitHub:**
- Visit: https://github.com
- Sign up or login
- Click "New repository"

### **2. Create Repository:**
- **Repository name**: `kg-injection-pipeline`
- **Description**: `Knowledge Graph Injection Pipeline for iFlow Processing`
- **Visibility**: Public (required for free Railway)
- Click "Create repository"

## 📦 **Step 2: Upload Your Code to GitHub**

### **Method 1: Using GitHub Web Interface**

1. **Go to your new repository**
2. **Click "uploading an existing file"**
3. **Upload these files:**
   - `app.py`
   - `kg_iflow.py`
   - `requirements.txt`
   - `runtime.txt`
   - `Procfile`

### **Method 2: Using Git Commands**

```bash
# Navigate to your project directory
cd "C:\Users\durai\OneDrive\Desktop\ITR\Injection Pipeline KG"

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Knowledge Graph Injection Pipeline"

# Add GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/kg-injection-pipeline.git

# Push to GitHub
git push -u origin main
```

## 🚀 **Step 3: Deploy on Railway**

### **1. Go to Railway:**
- Visit: https://railway.app
- Login with GitHub account

### **2. Create New Project:**
- Click "New Project"
- Select "Deploy from GitHub repo"
- Select your `kg-injection-pipeline` repository

### **3. Configure Environment Variables:**
In Railway dashboard, go to "Variables" tab and add:
```
NEO4J_URI = neo4j+s://2dcc1deb.databases.neo4j.io
NEO4J_USERNAME = neo4j
NEO4J_PASSWORD = S9izBZWrxQRGtPWCy4npV07xnDZoeHAqFXaBJNGVWHY
NEO4J_DATABASE = neo4j
AURA_INSTANCEID = 2dcc1deb
AURA_INSTANCENAME = Instance01
```

### **4. Deploy:**
- Railway will automatically detect your Python app
- It will install dependencies from `requirements.txt`
- It will use your `Procfile` to start the app

## 🌐 **Step 4: Access Your App**

Your app will be available at:
```
https://your-app-name.railway.app
```

## 🔧 **Step 5: Test Your Deployment**

1. **Health Check:**
   - Visit: `https://your-app-name.railway.app/health`

2. **Upload Test:**
   - Visit: `https://your-app-name.railway.app`
   - Upload a test iFlow zip file

## 🔄 **Step 6: Updates**

When you make changes:
1. Update your local files
2. Push to GitHub: `git push origin main`
3. Railway will automatically redeploy

---

**🎉 This method doesn't require CLI installation!**
