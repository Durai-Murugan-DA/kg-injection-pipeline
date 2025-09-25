#!/usr/bin/env python3
"""
Simple Hello World Flask app for testing Cloud Foundry deployment
"""

from flask import Flask
import os

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def hello_world():
    """Simple hello world endpoint"""
    return '''
    <html>
        <head>
            <title>Hello World - Cloud Foundry Test</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .success { color: #28a745; font-size: 24px; }
                .info { color: #6c757d; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="success">🎉 Hello World from Cloud Foundry!</h1>
                <p class="info">
                    This is a simple Flask app deployed to SAP Cloud Foundry.<br>
                    If you can see this, the deployment was successful!
                </p>
                <p class="info">
                    <strong>Environment:</strong> SAP BTP Cloud Foundry<br>
                    <strong>Runtime:</strong> Python Flask<br>
                    <strong>Status:</strong> ✅ Running
                </p>
            </div>
        </body>
    </html>
    '''

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'message': 'Hello World app is running!'}

@app.route('/api/info')
def api_info():
    """API info endpoint"""
    return {
        'app': 'Hello World',
        'version': '1.0.0',
        'status': 'running',
        'environment': 'SAP Cloud Foundry'
    }

if __name__ == '__main__':
    # Get port from environment variable (Cloud Foundry sets this)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

