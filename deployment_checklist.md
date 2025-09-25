# ✅ SAP Cloud Foundry Deployment Checklist

## **Pre-Deployment Checklist**

### **1. Prerequisites**
- [ ] SAP Cloud Foundry account created
- [ ] Cloud Foundry CLI installed (`cf --version`)
- [ ] Neo4j Aura credentials ready
- [ ] Application files ready in project directory

### **2. Environment Setup**
- [ ] Login to Cloud Foundry (`cf login`)
- [ ] Select correct organization and space
- [ ] Set Neo4j environment variables
- [ ] Verify manifest.yml configuration

### **3. Application Files**
- [ ] `app.py` - Main Flask application
- [ ] `kg_iflow.py` - Knowledge Graph logic
- [ ] `requirements.txt` - Python dependencies
- [ ] `Procfile` - Process definition
- [ ] `manifest.yml` - Cloud Foundry configuration
- [ ] `gunicorn.conf.py` - Gunicorn configuration
- [ ] `runtime.txt` - Python version
- [ ] `.cfignore` - Ignore file

---

## **Deployment Steps**

### **Step 1: Login**
```bash
cf login -a https://api.cf.sap.hana.ondemand.com
```

### **Step 2: Set Environment Variables**
```bash
cf set-env kg-injection-pipeline NEO4J_URI "neo4j+s://your-instance.databases.neo4j.io"
cf set-env kg-injection-pipeline NEO4J_USERNAME "neo4j"
cf set-env kg-injection-pipeline NEO4J_PASSWORD "your-password"
cf set-env kg-injection-pipeline NEO4J_DATABASE "neo4j"
```

### **Step 3: Deploy**
```bash
cf push
```

### **Step 4: Verify**
```bash
cf apps
cf logs kg-injection-pipeline
```

---

## **Post-Deployment Checklist**

### **1. Application Status**
- [ ] Application deployed successfully
- [ ] No build errors in logs
- [ ] Application is running (status: running)
- [ ] Health check endpoint responding

### **2. Functionality Test**
- [ ] Web interface accessible
- [ ] Upload endpoint working
- [ ] Neo4j connection established
- [ ] Knowledge Graph creation working
- [ ] Protocol nodes being created
- [ ] Folder isolation working

### **3. Performance Check**
- [ ] Application responds within 5 seconds
- [ ] File uploads working
- [ ] Database queries executing
- [ ] No memory issues

---

## **Troubleshooting Checklist**

### **If Deployment Fails:**
- [ ] Check Cloud Foundry CLI version
- [ ] Verify login status (`cf target`)
- [ ] Check manifest.yml syntax
- [ ] Verify environment variables
- [ ] Check buildpack compatibility

### **If Application Crashes:**
- [ ] Check application logs (`cf logs`)
- [ ] Verify Neo4j connection
- [ ] Check environment variables
- [ ] Increase memory allocation
- [ ] Check Python version compatibility

### **If Performance Issues:**
- [ ] Scale application (`cf scale`)
- [ ] Increase memory allocation
- [ ] Check Neo4j connection pool
- [ ] Monitor resource usage

---

## **Production Readiness**

### **Security**
- [ ] Environment variables secured
- [ ] HTTPS enabled
- [ ] Secret keys set
- [ ] Database credentials protected

### **Monitoring**
- [ ] Application logs configured
- [ ] Health checks enabled
- [ ] Performance monitoring set up
- [ ] Error tracking configured

### **Scaling**
- [ ] Multiple instances configured
- [ ] Load balancing enabled
- [ ] Auto-scaling rules set
- [ ] Resource limits defined

---

## **Quick Commands Reference**

```bash
# Deploy
cf push

# Check status
cf apps
cf app kg-injection-pipeline

# View logs
cf logs kg-injection-pipeline
cf logs kg-injection-pipeline --recent

# Restart
cf restart kg-injection-pipeline

# Scale
cf scale kg-injection-pipeline -i 2 -m 2G

# Environment
cf env kg-injection-pipeline
cf set-env kg-injection-pipeline VAR_NAME "value"

# Delete
cf delete kg-injection-pipeline
```

---

## **Success Criteria**

✅ **Application deployed successfully**  
✅ **Web interface accessible**  
✅ **File uploads working**  
✅ **Knowledge Graph creation successful**  
✅ **Protocol nodes included**  
✅ **Folder isolation working**  
✅ **No critical errors in logs**  
✅ **Performance acceptable**  

---

## **Next Steps After Deployment**

1. **Test with real iFlow files**
2. **Monitor application performance**
3. **Set up monitoring and alerting**
4. **Configure backup and recovery**
5. **Document operational procedures**
6. **Train users on the application**



