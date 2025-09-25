#!/bin/bash
# SAP Cloud Foundry Deployment Script for KG Injection Pipeline

echo "🚀 Starting SAP Cloud Foundry Deployment..."
echo "=============================================="

# Step 1: Check if CF CLI is installed
echo "📋 Step 1: Checking Cloud Foundry CLI..."
if ! command -v cf &> /dev/null; then
    echo "❌ Cloud Foundry CLI not found!"
    echo "Please install it from: https://github.com/cloudfoundry/cli/releases"
    exit 1
fi
echo "✅ Cloud Foundry CLI found: $(cf --version)"

# Step 2: Check if logged in
echo ""
echo "📋 Step 2: Checking Cloud Foundry login status..."
if ! cf target &> /dev/null; then
    echo "❌ Not logged in to Cloud Foundry!"
    echo "Please run: cf login -a https://api.cf.sap.hana.ondemand.com"
    exit 1
fi
echo "✅ Logged in to Cloud Foundry"

# Step 3: Set environment variables
echo ""
echo "📋 Step 3: Setting environment variables..."
echo "Please set your Neo4j credentials as environment variables:"
echo ""
echo "export NEO4J_URI='neo4j+s://your-instance.databases.neo4j.io'"
echo "export NEO4J_USERNAME='neo4j'"
echo "export NEO4J_PASSWORD='your-password'"
echo "export NEO4J_DATABASE='neo4j'"
echo ""
echo "Press Enter when you've set the environment variables..."
read

# Step 4: Deploy the application
echo ""
echo "📋 Step 4: Deploying application to Cloud Foundry..."
cf push

# Step 5: Check deployment status
echo ""
echo "📋 Step 5: Checking deployment status..."
cf apps

echo ""
echo "🎉 Deployment completed!"
echo "Your application should be available at:"
echo "https://kg-injection-pipeline.cfapps.sap.hana.ondemand.com"
echo ""
echo "📊 To check logs: cf logs kg-injection-pipeline"
echo "🔄 To restart: cf restart kg-injection-pipeline"
echo "🗑️ To delete: cf delete kg-injection-pipeline"


