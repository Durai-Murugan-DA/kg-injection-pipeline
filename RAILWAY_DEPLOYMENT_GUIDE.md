# 🚀 Railway Deployment Guide for Knowledge Graph Injection Pipeline

## 📋 **Why Railway?**
- ✅ **Free tier available** - No payment verification required
- ✅ **Easy deployment** - Similar to Heroku but more generous
- ✅ **Built-in databases** - Can add PostgreSQL, Redis, etc.
- ✅ **Simple CLI** - Easy to use

## 🔧 **Step 1: Install Railway CLI**

### **Windows:**
```bash
# Using npm (if you have Node.js installed)
npm install -g @railway/cli

# Or download from: https://railway.app/cli
```

### **Alternative - Direct Download:**
1. Go to [railway.app/cli](https://railway.app/cli)
2. Download the Windows installer
3. Run the installer

## 🔐 **Step 2: Login to Railway**

```bash
railway login
```
- This will open your browser to authenticate
- Sign up with GitHub, Google, or email

## 📁 **Step 3: Prepare Your Project**

### **Current Project Structure:**
```
KG_INJECTION_PIPELINE/
├── app.py                 # Main Flask application
├── kg_iflow.py           # Knowledge Graph logic
├── Procfile              # Process definition (Railway uses this too)
├── requirements.txt      # Python dependencies
├── runtime.txt           # Python version
└── uploads/              # Upload directory (created automatically)
```

## 🚀 **Step 4: Create Railway Project**

```bash
# Navigate to your project directory
cd "C:\Users\durai\OneDrive\Desktop\ITR\Injection Pipeline KG"

# Initialize Railway project
railway init

# This will create a railway.json file
```

## 🔑 **Step 5: Set Environment Variables**

```bash
# Set Neo4j connection details
railway variables set NEO4J_URI="neo4j+s://2dcc1deb.databases.neo4j.io"
railway variables set NEO4J_USERNAME="neo4j"
railway variables set NEO4J_PASSWORD="S9izBZWrxQRGtPWCy4npV07xnDZoeHAqFXaBJNGVWHY"
railway variables set NEO4J_DATABASE="neo4j"
railway variables set AURA_INSTANCEID="2dcc1deb"
railway variables set AURA_INSTANCENAME="Instance01"
```

### **Verify Environment Variables:**
```bash
railway variables
```

## 📦 **Step 6: Deploy to Railway**

```bash
# Deploy the application
railway up
```

## 🔍 **Step 7: Get Your App URL**

```bash
# Get the deployment URL
railway domain
```

## 🌐 **Step 8: Access Your Application**

Your app will be available at the URL provided by Railway (something like):
```
https://your-app-name.railway.app
```

## 🔧 **Step 9: Test Your Deployment**

### **1. Health Check:**
```bash
curl https://your-app-name.railway.app/health
```

### **2. Upload Test:**
1. Open your browser to the Railway URL
2. Upload a test iFlow zip file
3. Check the logs: `railway logs`

## 🛠️ **Troubleshooting**

### **Common Commands:**

```bash
# View logs
railway logs

# Check status
railway status

# Restart the app
railway restart

# View project info
railway info
```

## 🔄 **Updating Your App**

When you make changes to your code:

```bash
# Deploy updates
railway up
```

## 💰 **Railway Pricing**

- **Free Tier**: $5 credit monthly (enough for small apps)
- **Pro Plan**: $5/month for more resources
- **No payment verification required for free tier**

---

**🎉 Railway is a great alternative to Heroku with a generous free tier!**
