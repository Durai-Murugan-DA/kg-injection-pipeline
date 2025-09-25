# 🚀 SAP Cloud Foundry Deployment Guide

## **Complete Step-by-Step Deployment Instructions**

### **Prerequisites**
- ✅ SAP Cloud Foundry account
- ✅ Cloud Foundry CLI installed
- ✅ Neo4j Aura credentials ready

---

## **Step 1: Install Cloud Foundry CLI**

### **Windows:**
```bash
# Option 1: Download from GitHub
# Visit: https://github.com/cloudfoundry/cli/releases
# Download the Windows installer

# Option 2: Using Chocolatey
choco install cf-cli

# Option 3: Using Scoop
scoop install cf
```

### **Verify Installation:**
```bash
cf --version
```

---

## **Step 2: Login to SAP Cloud Foundry**

```bash
# Login to SAP Cloud Foundry
cf login -a https://api.cf.sap.hana.ondemand.com

# Enter your credentials:
# Email: your-email@domain.com
# Password: your-password
# Organization: (select your org)
# Space: (select your space)
```

---

## **Step 3: Set Environment Variables**

### **Option A: Set in Cloud Foundry (Recommended)**
```bash
# Set your Neo4j credentials
cf set-env kg-injection-pipeline NEO4J_URI "neo4j+s://your-instance.databases.neo4j.io"
cf set-env kg-injection-pipeline NEO4J_USERNAME "neo4j"
cf set-env kg-injection-pipeline NEO4J_PASSWORD "your-password"
cf set-env kg-injection-pipeline NEO4J_DATABASE "neo4j"
```

### **Option B: Set Locally (for testing)**
```bash
# Windows Command Prompt
set NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
set NEO4J_USERNAME=neo4j
set NEO4J_PASSWORD=your-password
set NEO4J_DATABASE=neo4j

# Windows PowerShell
$env:NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io"
$env:NEO4J_USERNAME="neo4j"
$env:NEO4J_PASSWORD="your-password"
$env:NEO4J_DATABASE="neo4j"
```

---

## **Step 4: Deploy the Application**

### **Quick Deployment:**
```bash
# Deploy using the manifest file
cf push
```

### **Manual Deployment:**
```bash
# Deploy with specific settings
cf push kg-injection-pipeline \
  --manifest manifest.yml \
  --memory 1G \
  --instances 1
```

---

## **Step 5: Verify Deployment**

### **Check Application Status:**
```bash
# List all applications
cf apps

# Check application details
cf app kg-injection-pipeline

# View application logs
cf logs kg-injection-pipeline
```

### **Test the Application:**
```bash
# Get the application URL
cf app kg-injection-pipeline

# Test the health endpoint
curl https://kg-injection-pipeline.cfapps.sap.hana.ondemand.com/health
```

---

## **Step 6: Access Your Application**

### **Application URL:**
```
https://kg-injection-pipeline.cfapps.sap.hana.ondemand.com
```

### **Available Endpoints:**
- **Main Interface**: `/` - Upload interface
- **Health Check**: `/health` - Application status
- **Upload**: `/upload` - POST endpoint for file uploads
- **Status**: `/status` - Database statistics
- **Export**: `/export` - Export graph data

---

## **Step 7: Monitor and Manage**

### **View Logs:**
```bash
# Real-time logs
cf logs kg-injection-pipeline

# Recent logs
cf logs kg-injection-pipeline --recent
```

### **Restart Application:**
```bash
cf restart kg-injection-pipeline
```

### **Scale Application:**
```bash
# Scale to 2 instances
cf scale kg-injection-pipeline -i 2

# Scale memory to 2GB
cf scale kg-injection-pipeline -m 2G
```

### **Update Environment Variables:**
```bash
cf set-env kg-injection-pipeline NEO4J_PASSWORD "new-password"
cf restart kg-injection-pipeline
```

---

## **Step 8: Troubleshooting**

### **Common Issues:**

#### **1. Buildpack Issues:**
```bash
# Specify Python buildpack explicitly
cf push -b python_buildpack
```

#### **2. Memory Issues:**
```bash
# Increase memory
cf scale kg-injection-pipeline -m 2G
```

#### **3. Environment Variables:**
```bash
# Check environment variables
cf env kg-injection-pipeline

# Set missing variables
cf set-env kg-injection-pipeline VARIABLE_NAME "value"
```

#### **4. Application Crashes:**
```bash
# Check logs for errors
cf logs kg-injection-pipeline --recent

# Restart application
cf restart kg-injection-pipeline
```

---

## **Step 9: Production Optimization**

### **Performance Tuning:**
```bash
# Scale for production
cf scale kg-injection-pipeline -i 3 -m 2G

# Set production environment variables
cf set-env kg-injection-pipeline FLASK_ENV "production"
cf set-env kg-injection-pipeline DEBUG "false"
```

### **Security:**
```bash
# Enable HTTPS only
cf set-env kg-injection-pipeline FORCE_HTTPS "true"

# Set secure session settings
cf set-env kg-injection-pipeline SECRET_KEY "your-secret-key"
```

---

## **Step 10: Cleanup (if needed)**

### **Delete Application:**
```bash
cf delete kg-injection-pipeline
```

### **Delete Service Bindings:**
```bash
cf unbind-service kg-injection-pipeline neo4j-service
```

---

## **🎉 Success!**

Your Knowledge Graph injection pipeline is now deployed on SAP Cloud Foundry!

### **Next Steps:**
1. **Test the application** using the web interface
2. **Upload iFlow files** to create Knowledge Graphs
3. **Monitor performance** using Cloud Foundry tools
4. **Scale as needed** based on usage

### **Support:**
- **Cloud Foundry Docs**: https://docs.cloudfoundry.org/
- **SAP Cloud Foundry**: https://help.sap.com/viewer/65de2977205c403bbc107264b8eccf4b/
- **Neo4j Aura**: https://neo4j.com/cloud/aura/

---

## **Quick Reference Commands:**

```bash
# Deploy
cf push

# Check status
cf apps

# View logs
cf logs kg-injection-pipeline

# Restart
cf restart kg-injection-pipeline

# Scale
cf scale kg-injection-pipeline -i 2 -m 2G

# Delete
cf delete kg-injection-pipeline
```