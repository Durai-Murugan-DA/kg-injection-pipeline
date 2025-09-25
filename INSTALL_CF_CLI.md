# 🚀 How to Install Cloud Foundry CLI on Windows

## **Method 1: Direct Download (Recommended)**

### **Step 1: Download the Installer**
1. Go to: https://github.com/cloudfoundry/cli/releases
2. Look for the latest release (e.g., v8.x.x)
3. Download the Windows installer: `cf-windows-amd64.msi`

### **Step 2: Install**
1. Run the downloaded `.msi` file
2. Follow the installation wizard
3. The CLI will be automatically added to your PATH

### **Step 3: Verify Installation**
Open a new Command Prompt or PowerShell and run:
```bash

```

---

## **Method 2: Manual Download**

### **Step 1: Download Executable**
1. Go to: https://github.com/cloudfoundry/cli/releases
2. Download: `cf-windows-amd64.exe`
3. Save it to a folder (e.g., `C:\cf-cli\`)

### **Step 2: Add to PATH**
1. Open System Properties → Environment Variables
2. Add `C:\cf-cli\` to your PATH
3. Restart Command Prompt

### **Step 3: Verify**
```bash
cf --version
```

---

## **Method 3: Using Package Managers**

### **If you have Chocolatey installed:**
```bash
choco install cf-cli
```

### **If you have Scoop installed:**
```bash
scoop install cf
```

### **If you have Winget installed:**
```bash
winget install CloudFoundry.cli
```

---

## **Troubleshooting**

### **If `cf` command not found:**
1. **Check PATH**: Make sure the CF CLI directory is in your PATH
2. **Restart Terminal**: Close and reopen your command prompt
3. **Check Installation**: Verify the file exists in the installation directory

### **If download fails:**
1. **Try different browser**: Sometimes browser security blocks downloads
2. **Use direct link**: https://github.com/cloudfoundry/cli/releases/latest
3. **Check antivirus**: Some antivirus software blocks executable downloads

### **If installation fails:**
1. **Run as Administrator**: Right-click installer → "Run as administrator"
2. **Check Windows version**: Ensure you have Windows 10/11
3. **Check architecture**: Download the correct version (amd64 for most systems)

---

## **Quick Test After Installation**

Once installed, test with these commands:

```bash
# Check version
cf --version

# Check help
cf help

# List available commands
cf commands
```

---

## **Next Steps After Installation**

1. **Login to SAP Cloud Foundry:**
   ```bash
   cf login -a https://api.cf.sap.hana.ondemand.com
   ```

2. **Deploy your application:**
   ```bash
   cf push
   ```

---

## **Alternative: Use Docker (If CLI installation fails)**

If you can't install the CLI directly, you can use Docker:

```bash
# Run CF CLI in Docker container
docker run -it --rm -v ${PWD}:/workspace cloudfoundry/cf-cli:latest

# Then use cf commands inside the container
cf login -a https://api.cf.sap.hana.ondemand.com
```

---

## **Need Help?**

- **GitHub Issues**: https://github.com/cloudfoundry/cli/issues
- **SAP Documentation**: https://help.sap.com/viewer/65de2977205c403bbc107264b8eccf4b/
- **Cloud Foundry Docs**: https://docs.cloudfoundry.org/cf-cli/



