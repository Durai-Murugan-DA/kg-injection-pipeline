#!/usr/bin/env python3
"""
SAP Integration Flow Knowledge Graph Injection Pipeline
Flask application for uploading iFlow folders and generating Knowledge Graphs in Neo4j.
"""

import os
import zipfile
import tempfile
import shutil
import logging
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import json
from datetime import datetime
import traceback

# Import the KG creation logic
from kg_iflow import IFlowKnowledgeGraph

# Load environment variables from config.env (for local development)
# In Heroku, environment variables are set directly
from dotenv import load_dotenv
import os

# Try to load config.env for local development, but don't fail if it doesn't exist
if os.path.exists('config.env'):
    load_dotenv('config.env')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'zip'}

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def extract_folder_name_from_zip(zip_path):
    """Extract the folder name from a zip file by examining its contents."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get all file names in the zip
            file_names = zip_ref.namelist()
            
            if not file_names:
                logger.warning("Empty zip file")
                return None
            
            logger.info(f"Analyzing zip file contents: {len(file_names)} files")
            logger.info(f"Sample files: {file_names[:5]}")
            
            # Strategy 1: Look for the most meaningful root folder
            root_folders = set()
            for file_name in file_names:
                if '/' in file_name:
                    root_folder = file_name.split('/')[0]
                    # Skip common technical folders
                    if root_folder.lower() not in ['src', 'target', 'build', 'bin', 'lib', 'resources', 'meta-inf', 'web-inf']:
                        root_folders.add(root_folder)
            
            if root_folders:
                # Choose the most meaningful folder name
                folder_name = choose_best_folder_name(list(root_folders))
                logger.info(f"Found root folder in zip: {folder_name}")
                
                # Clean up the folder name
                folder_name = clean_folder_name(folder_name)
                
                if folder_name and len(folder_name) > 2:
                    return folder_name
            
            # Strategy 2: Look for .iflw files to determine the flow name
            logger.info("No clear folder structure found, analyzing .iflw files")
            iflow_files = [f for f in file_names if f.endswith('.iflw')]
            if iflow_files:
                # Extract name from .iflw file
                iflow_file = iflow_files[0]
                iflow_name = os.path.splitext(os.path.basename(iflow_file))[0]
                logger.info(f"Found iFlow file: {iflow_name}")
                
                # Clean up the name
                iflow_name = clean_folder_name(iflow_name)
                
                if iflow_name and len(iflow_name) > 2:
                    return iflow_name
            
            # Strategy 3: Look for other meaningful files
            meaningful_files = [f for f in file_names if any(ext in f.lower() for ext in ['.xml', '.json', '.properties', '.config'])]
            if meaningful_files:
                # Try to extract name from meaningful files
                for file_path in meaningful_files:
                    if '/' in file_path:
                        folder_name = file_path.split('/')[0]
                        if folder_name.lower() not in ['src', 'target', 'build', 'bin', 'lib', 'resources', 'meta-inf', 'web-inf']:
                            folder_name = clean_folder_name(folder_name)
                            if folder_name and len(folder_name) > 2:
                                logger.info(f"Found meaningful folder from file: {folder_name}")
                                return folder_name
            
            # Strategy 4: Fallback to zip filename
            zip_basename = os.path.splitext(os.path.basename(zip_path))[0]
            # Remove timestamp prefix if present
            if '_' in zip_basename:
                parts = zip_basename.split('_')
                if len(parts) > 1 and parts[0].isdigit():
                    # Remove timestamp prefix
                    zip_basename = '_'.join(parts[1:])
            
            zip_basename = clean_folder_name(zip_basename)
            
            if zip_basename and len(zip_basename) > 2:
                logger.info(f"Using zip filename: {zip_basename}")
                return zip_basename
            
            # Final fallback
            logger.warning("Could not extract meaningful folder name, using default")
            return "iFlow Integration"
                
    except Exception as e:
        logger.error(f"Error extracting folder name from zip: {e}")
        return None

def choose_best_folder_name(folder_names):
    """Choose the most meaningful folder name from a list."""
    # Prioritize folders that look like actual iFlow names
    meaningful_folders = []
    
    for folder in folder_names:
        # Skip very short names
        if len(folder) < 3:
            continue
        
        # Skip common technical folders
        if folder.lower() in ['src', 'target', 'build', 'bin', 'lib', 'resources', 'meta-inf', 'web-inf']:
            continue
        
        # Prefer folders with descriptive names
        if any(word in folder.lower() for word in ['flow', 'integration', 'process', 'service', 'api', 'data', 'customer', 'order', 'material', 'product']):
            meaningful_folders.insert(0, folder)  # Put at front
        else:
            meaningful_folders.append(folder)
    
    return meaningful_folders[0] if meaningful_folders else folder_names[0] if folder_names else "iFlow Integration"

def clean_folder_name(folder_name):
    """Clean up a folder name by removing common prefixes/suffixes and formatting."""
    if not folder_name:
        return None
    
    # Replace underscores with spaces
    folder_name = folder_name.replace('_', ' ').strip()
    
    # Remove multiple spaces
    folder_name = ' '.join(folder_name.split())
    
    # Remove common SAP/iFlow prefixes and suffixes
    prefixes_to_remove = [
        'iflow', 'iFlow', 'integration flow', 'integrationflow',
        'sap', 'SAP', 'flow', 'Flow', 'integration', 'Integration'
    ]
    
    suffixes_to_remove = [
        'iflow', 'iFlow', 'flow', 'Flow', 'integration', 'Integration'
    ]
    
    # Remove prefixes
    for prefix in prefixes_to_remove:
        if folder_name.lower().startswith(prefix.lower()):
            folder_name = folder_name[len(prefix):].strip()
            break
    
    # Remove suffixes
    for suffix in suffixes_to_remove:
        if folder_name.lower().endswith(suffix.lower()):
            folder_name = folder_name[:-len(suffix)].strip()
            break
    
    # Clean up any remaining issues
    folder_name = ' '.join(folder_name.split())
    
    # If the name is too short or empty, return None
    if len(folder_name) < 3:
        return None
    
    return folder_name

def extract_zip_file(zip_path, extract_to):
    """Extract a zip file to the specified directory."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        logger.info(f"Successfully extracted {zip_path} to {extract_to}")
        return True
    except Exception as e:
        logger.error(f"Error extracting zip file: {e}")
        return False

def find_iflow_file(extracted_path):
    """Find the iFlow file in the extracted directory structure."""
    iflow_patterns = [
        "src/main/resources/scenarioflows/integrationflow/*.iflw",
        "**/*.iflw",
        "**/integrationflow/*.iflw"
    ]
    
    for root, dirs, files in os.walk(extracted_path):
        for file in files:
            if file.endswith('.iflw'):
                iflow_path = os.path.join(root, file)
                logger.info(f"Found iFlow file: {iflow_path}")
                return iflow_path
    
    logger.warning("No .iflw file found in the extracted directory")
    return None

def process_iflow_folder(extracted_path, folder_name=None):
    """Process the iFlow folder and create the Knowledge Graph."""
    try:
        # Find the iFlow file
        iflow_file = find_iflow_file(extracted_path)
        if not iflow_file:
            return {
                'success': False,
                'error': 'No .iflw file found in the uploaded folder'
            }
        
        # Use provided folder name or extract from path
        if not folder_name:
            folder_name = os.path.basename(extracted_path) or "Uploaded_iFlow"
        
        logger.info(f"Original folder name: '{folder_name}'")
        
        # Clean up the folder name - replace underscores with spaces and clean up
        folder_name = folder_name.replace('_', ' ').strip()
        # Remove any extra spaces but keep meaningful characters
        folder_name = ' '.join(folder_name.split())
        # Only remove truly problematic characters, keep meaningful business names
        folder_name = ''.join(c for c in folder_name if c.isalnum() or c in [' ', '-', '(', ')', '&', '/']).strip()
        if not folder_name:
            folder_name = "Uploaded iFlow"
        
        logger.info(f"Final folder name: '{folder_name}'")
        
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy the iFlow file to the expected location
            target_iflow_path = os.path.join(temp_dir, "src/main/resources/scenarioflows/integrationflow/test_iflow.iflw")
            os.makedirs(os.path.dirname(target_iflow_path), exist_ok=True)
            shutil.copy2(iflow_file, target_iflow_path)
            
            # Initialize the Knowledge Graph creator with folder name
            kg = IFlowKnowledgeGraph(folder_name=folder_name)
            kg.iflow_file = target_iflow_path
            
            # Create the Knowledge Graph
            kg.run()
            
            # Get statistics
            stats = kg.get_graph_statistics()
            
            return {
                'success': True,
                'message': 'Knowledge Graph created successfully',
                'statistics': stats,
                'iflow_file': iflow_file,
                'folder_name': folder_name
            }
            
    except Exception as e:
        logger.error(f"Error processing iFlow folder: {e}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': f'Error processing iFlow folder: {str(e)}'
        }

@app.route('/')
def index():
    """Main page with upload interface."""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>KG Injection Pipeline</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; border-radius: 10px; }
            .upload-area:hover { border-color: #007bff; background-color: #f8f9fa; }
            input[type="file"] { margin: 20px 0; }
            button { background-color: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background-color: #0056b3; }
            button:disabled { background-color: #ccc; cursor: not-allowed; }
            .result { margin-top: 20px; padding: 15px; border-radius: 5px; }
            .success { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            .error { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
            .loading { background-color: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }
            .stats { background-color: #e2e3e5; border: 1px solid #d6d8db; color: #383d41; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 KG Injection Pipeline</h1>
            <p style="text-align: center; color: #666;">Upload your iFlow zip file to generate a Knowledge Graph</p>
            
            <div class="upload-area">
                <h3>📁 Upload iFlow Folder</h3>
                <p>Select a zip file containing your iFlow folder</p>
                <form id="uploadForm" enctype="multipart/form-data">
                    <input type="file" id="fileInput" name="file" accept=".zip" required>
                    <br><br>
                    <button type="submit" id="uploadBtn">🚀 Generate Knowledge Graph</button>
                </form>
            </div>
            
            <div id="result"></div>
            
            <div style="margin-top: 30px; text-align: center;">
                <h3>📊 Quick Actions</h3>
                <button onclick="checkStatus()">📈 Check Database Status</button>
                <button onclick="exportGraph()">📥 Export Graph Data</button>
                <button onclick="clearDatabase()" style="background-color: #dc3545;">🗑️ Clear Database</button>
            </div>
        </div>

        <script>
            document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const fileInput = document.getElementById('fileInput');
                const uploadBtn = document.getElementById('uploadBtn');
                const resultDiv = document.getElementById('result');
                
                if (!fileInput.files[0]) {
                    showResult('Please select a file to upload.', 'error');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                uploadBtn.disabled = true;
                uploadBtn.textContent = '⏳ Processing...';
                showResult('Uploading and processing your iFlow file...', 'loading');
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        showResult(`✅ ${result.message}`, 'success');
                        if (result.statistics) {
                            showStats(result.statistics);
                        }
                    } else {
                        if (result.error_type === 'duplicate_folder') {
                            showResult(`⚠️ ${result.error}<br><br>💡 <strong>Solutions:</strong><br>• Use a different folder name<br>• Clear the existing folder first<br>• Rename your zip file`, 'error');
                        } else {
                            showResult(`❌ Error: ${result.error}`, 'error');
                        }
                    }
                } catch (error) {
                    showResult(`❌ Upload failed: ${error.message}`, 'error');
                } finally {
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = '🚀 Generate Knowledge Graph';
                }
            });
            
            function showResult(message, type) {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = `<div class="result ${type}">${message}</div>`;
            }
            
            function showStats(stats) {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML += `
                    <div class="stats">
                        <h4>📊 Knowledge Graph Statistics</h4>
                        <p><strong>Total Nodes:</strong> ${stats.total_nodes}</p>
                        <p><strong>Total Relationships:</strong> ${stats.total_relationships}</p>
                        <p><strong>Nodes by Type:</strong></p>
                        <ul>
                            ${Object.entries(stats.nodes_by_type).map(([type, count]) => 
                                `<li>${type}: ${count}</li>`
                            ).join('')}
                        </ul>
                    </div>
                `;
            }
            
            async function checkStatus() {
                try {
                    const response = await fetch('/status');
                    const result = await response.json();
                    if (result.success) {
                        showResult(`📈 Database Status: Connected<br>Nodes: ${result.current_counts.nodes}, Relationships: ${result.current_counts.relationships}`, 'success');
                    } else {
                        showResult(`❌ Database Error: ${result.error}`, 'error');
                    }
                } catch (error) {
                    showResult(`❌ Status check failed: ${error.message}`, 'error');
                }
            }
            
            async function exportGraph() {
                try {
                    const response = await fetch('/export');
                    if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'iflow_graph_export.json';
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        showResult('📥 Graph data exported successfully!', 'success');
                    } else {
                        showResult('❌ Export failed', 'error');
                    }
                } catch (error) {
                    showResult(`❌ Export failed: ${error.message}`, 'error');
                }
            }
            
            async function clearDatabase() {
                if (!confirm('⚠️ Are you sure you want to clear the database? This will delete all data!')) {
                    return;
                }
                
                try {
                    const response = await fetch('/clear', { method: 'POST' });
                    const result = await response.json();
                    if (result.success) {
                        showResult('🗑️ Database cleared successfully!', 'success');
                    } else {
                        showResult(`❌ Clear failed: ${result.error}`, 'error');
                    }
                } catch (error) {
                    showResult(`❌ Clear failed: ${error.message}`, 'error');
                }
            }
        </script>
    </body>
    </html>
    '''

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'KG Injection Pipeline',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/upload', methods=['POST'])
def upload_iflow():
    """
    Upload and process an iFlow folder (zipped).
    Expected: multipart/form-data with 'file' field containing a zip file.
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided in request'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Check if file has allowed extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'File must be a zip file (.zip)'
            }), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Extract the original folder name from the uploaded filename
        original_filename = secure_filename(file.filename)
        folder_name = original_filename.replace('.zip', '').replace('.ZIP', '')
        
        # Clean up the folder name - replace underscores with spaces and clean up
        folder_name = folder_name.replace('_', ' ').strip()
        # Remove any extra spaces
        folder_name = ' '.join(folder_name.split())
        
        # Save uploaded file
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        logger.info(f"File uploaded: {upload_path}")
        
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_extract_dir:
            # Extract the zip file
            if not extract_zip_file(upload_path, temp_extract_dir):
                return jsonify({
                    'success': False,
                    'error': 'Failed to extract zip file'
                }), 400
            
            # Process the extracted iFlow folder with the original folder name
            result = process_iflow_folder(temp_extract_dir, folder_name=folder_name)
            
            # Clean up uploaded file
            try:
                os.remove(upload_path)
                logger.info(f"Cleaned up uploaded file: {upload_path}")
            except Exception as e:
                logger.warning(f"Could not clean up uploaded file: {e}")
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': f'iFlow processed successfully and Knowledge Graph created for folder: {result.get("folder_name", "Unknown")}',
                    'statistics': result.get('statistics', {}),
                    'iflow_file': result.get('iflow_file', ''),
                    'folder_name': result.get('folder_name', ''),
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
            else:
                # Check if it's a duplicate folder error
                error_message = result.get('error', 'Unknown error occurred')
                if 'already exists' in error_message.lower():
                    return jsonify({
                        'success': False,
                        'error': f'Folder "{folder_name}" already exists in the database. Please use a different name or clear the existing folder first.',
                        'folder_name': folder_name,
                        'error_type': 'duplicate_folder'
                    }), 409  # Conflict status code
                else:
                    return jsonify({
                        'success': False,
                        'error': error_message
                    }), 500
                
    except RequestEntityTooLarge:
        return jsonify({
            'success': False,
            'error': 'File too large. Maximum size is 100MB.'
        }), 413
    
    except Exception as e:
        logger.error(f"Unexpected error in upload endpoint: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get the current status of the Knowledge Graph database."""
    try:
        kg = IFlowKnowledgeGraph()
        stats = kg.get_graph_statistics()
        counts = kg.get_current_counts()
        
        return jsonify({
            'success': True,
            'database_status': 'connected',
            'statistics': stats,
            'current_counts': counts,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        return jsonify({
            'success': False,
            'error': f'Database connection error: {str(e)}'
        }), 500

@app.route('/clear', methods=['POST'])
def clear_database():
    """Clear the Knowledge Graph database."""
    try:
        kg = IFlowKnowledgeGraph()
        kg.clear_database()
        
        return jsonify({
            'success': True,
            'message': 'Database cleared successfully',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        return jsonify({
            'success': False,
            'error': f'Error clearing database: {str(e)}'
        }), 500

@app.route('/clear-folder', methods=['POST'])
def clear_specific_folder():
    """Clear a specific folder from the Knowledge Graph database."""
    try:
        data = request.get_json()
        folder_name = data.get('folder_name')
        
        if not folder_name:
            return jsonify({
                'success': False,
                'error': 'Folder name is required'
            }), 400
        
        kg = IFlowKnowledgeGraph(folder_name=folder_name)
        kg.clear_folder_data()
        
        return jsonify({
            'success': True,
            'message': f'Folder "{folder_name}" cleared successfully',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error clearing folder: {e}")
        return jsonify({
            'success': False,
            'error': f'Error clearing folder: {str(e)}'
        }), 500

@app.route('/export', methods=['GET'])
def export_graph():
    """Export the current Knowledge Graph data as JSON."""
    try:
        kg = IFlowKnowledgeGraph()
        
        # Create export filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        export_filename = f"iflow_graph_export_{timestamp}.json"
        export_path = os.path.join(app.config['UPLOAD_FOLDER'], export_filename)
        
        # Export the graph data
        kg.export_graph_data(export_path)
        
        return send_file(
            export_path,
            as_attachment=True,
            download_name=export_filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"Error exporting graph: {e}")
        return jsonify({
            'success': False,
            'error': f'Error exporting graph: {str(e)}'
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 100MB.'
    }), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.route('/n8n/upload', methods=['POST'])
def upload_iflow_n8n():
    """
    Universal n8n-friendly endpoint for file uploads.
    Supports:
    1. Raw binary uploads (Content-Type: application/x-zip-compressed)
    2. Multipart/form-data uploads (Content-Type: multipart/form-data)
    3. JSON uploads with base64 data (Content-Type: application/json)
    """
    try:
        content_type = request.content_type or ''
        logger.info(f"Received upload request with Content-Type: {content_type}")
        
        # Handle different content types
        if 'application/x-zip-compressed' in content_type or 'application/octet-stream' in content_type:
            # Raw binary upload from n8n
            return handle_raw_binary_upload()
        elif 'multipart/form-data' in content_type:
            # Traditional multipart upload
            return handle_multipart_upload()
        elif 'application/json' in content_type:
            # JSON with base64 data
            return handle_json_upload()
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported Content-Type: {content_type}. Supported types: application/x-zip-compressed, multipart/form-data, application/json'
            }), 415
            
    except Exception as e:
        logger.error(f"Unexpected error in n8n upload endpoint: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

def handle_raw_binary_upload():
    """Handle raw binary file uploads from n8n."""
    try:
        # Get raw binary data
        file_data = request.get_data()
        
        if not file_data:
            return jsonify({
                'success': False,
                'error': 'No file data received'
            }), 400
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_n8n_upload.zip"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save raw binary data to file
        with open(temp_path, 'wb') as f:
            f.write(file_data)
        
        logger.info(f"Raw binary file saved: {temp_path} ({len(file_data)} bytes)")
        
        # Extract folder name from zip file contents
        folder_name = extract_folder_name_from_zip(temp_path)
        if not folder_name:
            folder_name = f"n8n_Upload_{timestamp}"
        
        logger.info(f"Extracted folder name: {folder_name}")
        
        # Process the file
        return process_uploaded_file(temp_path, folder_name)
        
    except Exception as e:
        logger.error(f"Error handling raw binary upload: {e}")
        return jsonify({
            'success': False,
            'error': f'Error processing raw binary upload: {str(e)}'
        }), 500

def handle_multipart_upload():
    """Handle traditional multipart/form-data uploads."""
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided in multipart request'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Check if file has allowed extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'File must be a zip file (.zip)'
            }), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        temp_filename = f"{timestamp}_{filename}"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        
        # Save uploaded file
        file.save(temp_path)
        logger.info(f"Multipart file saved: {temp_path}")
        
        # Extract folder name from zip file contents
        folder_name = extract_folder_name_from_zip(temp_path)
        if not folder_name:
            # Fallback to filename-based naming
            folder_name = filename.replace('.zip', '').replace('.ZIP', '')
            folder_name = folder_name.replace('_', ' ').strip()
            folder_name = ' '.join(folder_name.split())
            if not folder_name:
                folder_name = "Uploaded iFlow"
        
        logger.info(f"Extracted folder name: {folder_name}")
        
        # Process the file
        return process_uploaded_file(temp_path, folder_name)
        
    except Exception as e:
        logger.error(f"Error handling multipart upload: {e}")
        return jsonify({
            'success': False,
            'error': f'Error processing multipart upload: {str(e)}'
        }), 500

def handle_json_upload():
    """Handle JSON uploads with base64 data."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        if 'file_data' not in data:
            return jsonify({
                'success': False,
                'error': 'No file_data provided in JSON'
            }), 400
        
        # Get file information
        filename = data.get('filename', 'uploaded_file.zip')
        base64_data = data.get('file_data')
        
        if not base64_data:
            return jsonify({
                'success': False,
                'error': 'No base64 file data provided'
            }), 400
        
        # Decode base64 data
        import base64
        try:
            file_data = base64.b64decode(base64_data)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Invalid base64 data: {str(e)}'
            }), 400
        
        # Create temporary file
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        temp_filename = f"{timestamp}_{filename}"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        
        # Save decoded data to temporary file
        with open(temp_path, 'wb') as f:
            f.write(file_data)
        
        logger.info(f"JSON base64 file saved: {temp_path}")
        
        # Extract folder name from zip file contents
        folder_name = extract_folder_name_from_zip(temp_path)
        if not folder_name:
            # Fallback to filename-based naming
            folder_name = filename.replace('.zip', '').replace('.ZIP', '')
            folder_name = folder_name.replace('_', ' ').strip()
            folder_name = ' '.join(folder_name.split())
            if not folder_name:
                folder_name = "Uploaded iFlow"
        
        logger.info(f"Extracted folder name: {folder_name}")
        
        # Process the file
        return process_uploaded_file(temp_path, folder_name)
        
    except Exception as e:
        logger.error(f"Error handling JSON upload: {e}")
        return jsonify({
            'success': False,
            'error': f'Error processing JSON upload: {str(e)}'
        }), 500

def process_uploaded_file(file_path, folder_name):
    """Common processing logic for all upload types."""
    try:
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_extract_dir:
            # Extract the zip file
            if not extract_zip_file(file_path, temp_extract_dir):
                return jsonify({
                    'success': False,
                    'error': 'Failed to extract zip file'
                }), 400
            
            # Process the extracted iFlow folder
            result = process_iflow_folder(temp_extract_dir, folder_name=folder_name)
            
            # Clean up uploaded file
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up uploaded file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up uploaded file: {e}")
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': f'iFlow processed successfully and Knowledge Graph created for folder: {result.get("folder_name", "Unknown")}',
                    'statistics': result.get('statistics', {}),
                    'iflow_file': result.get('iflow_file', ''),
                    'folder_name': result.get('folder_name', ''),
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
            else:
                # Check if it's a duplicate folder error
                error_message = result.get('error', 'Unknown error occurred')
                if 'already exists' in error_message.lower():
                    return jsonify({
                        'success': False,
                        'error': f'Folder "{folder_name}" already exists in the database. Please use a different name or clear the existing folder first.',
                        'folder_name': folder_name,
                        'error_type': 'duplicate_folder'
                    }), 409  # Conflict status code
                else:
                    return jsonify({
                        'success': False,
                        'error': error_message
                    }), 500
                    
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        return jsonify({
            'success': False,
            'error': f'Error processing file: {str(e)}'
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_iflow_api():
    """
    API endpoint for direct file uploads (for n8n integration).
    Expected: multipart/form-data with 'file' field containing a zip file.
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided in request'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Check if file has allowed extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'File must be a zip file (.zip)'
            }), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Extract the original folder name from the uploaded filename
        original_filename = secure_filename(file.filename)
        folder_name = original_filename.replace('.zip', '').replace('.ZIP', '')
        
        # Clean up the folder name - replace underscores with spaces and clean up
        folder_name = folder_name.replace('_', ' ').strip()
        # Remove any extra spaces
        folder_name = ' '.join(folder_name.split())
        
        # Save uploaded file
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        logger.info(f"File uploaded: {upload_path}")
        
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_extract_dir:
            # Extract the zip file
            if not extract_zip_file(upload_path, temp_extract_dir):
                return jsonify({
                    'success': False,
                    'error': 'Failed to extract zip file'
                }), 400
            
            # Process the extracted iFlow folder with the original folder name
            result = process_iflow_folder(temp_extract_dir, folder_name=folder_name)
            
            # Clean up uploaded file
            try:
                os.remove(upload_path)
                logger.info(f"Cleaned up uploaded file: {upload_path}")
            except Exception as e:
                logger.warning(f"Could not clean up uploaded file: {e}")
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': f'iFlow processed successfully and Knowledge Graph created for folder: {result.get("folder_name", "Unknown")}',
                    'statistics': result.get('statistics', {}),
                    'iflow_file': result.get('iflow_file', ''),
                    'folder_name': result.get('folder_name', ''),
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
            else:
                # Check if it's a duplicate folder error
                error_message = result.get('error', 'Unknown error occurred')
                if 'already exists' in error_message.lower():
                    return jsonify({
                        'success': False,
                        'error': f'Folder "{folder_name}" already exists in the database. Please use a different name or clear the existing folder first.',
                        'folder_name': folder_name,
                        'error_type': 'duplicate_folder'
                    }), 409  # Conflict status code
                else:
                    return jsonify({
                        'success': False,
                        'error': error_message
                    }), 500
                
    except RequestEntityTooLarge:
        return jsonify({
            'success': False,
            'error': 'File too large. Maximum size is 100MB.'
        }), 413
    
    except Exception as e:
        logger.error(f"Unexpected error in upload API endpoint: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/upload-base64', methods=['POST'])
def upload_iflow_base64():
    """
    Upload and process an iFlow folder using base64 encoded data.
    Expected: JSON with 'data' field containing base64 encoded zip file.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        if 'data' not in data:
            return jsonify({
                'success': False,
                'error': 'No file data provided in JSON'
            }), 400
        
        # Get file information
        filename = data.get('filename', 'uploaded_file.zip')
        mime_type = data.get('mimeType', 'application/zip')
        base64_data = data.get('data')
        
        if not base64_data:
            return jsonify({
                'success': False,
                'error': 'No base64 data provided'
            }), 400
        
        # Decode base64 data
        import base64
        try:
            file_data = base64.b64decode(base64_data)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Invalid base64 data: {str(e)}'
            }), 400
        
        # Create temporary file
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        temp_filename = f"{timestamp}_{filename}"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        
        # Save decoded data to temporary file
        with open(temp_path, 'wb') as f:
            f.write(file_data)
        
        logger.info(f"Base64 file saved: {temp_path}")
        
        # Extract folder name from filename
        folder_name = filename.replace('.zip', '').replace('.ZIP', '')
        folder_name = folder_name.replace('_', ' ').strip()
        folder_name = ' '.join(folder_name.split())
        if not folder_name:
            folder_name = "Uploaded iFlow"
        
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_extract_dir:
            # Extract the zip file
            if not extract_zip_file(temp_path, temp_extract_dir):
                return jsonify({
                    'success': False,
                    'error': 'Failed to extract zip file'
                }), 400
            
            # Process the extracted iFlow folder
            result = process_iflow_folder(temp_extract_dir, folder_name=folder_name)
            
            # Clean up temporary file
            try:
                os.remove(temp_path)
                logger.info(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                logger.warning(f"Could not clean up temporary file: {e}")
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': f'iFlow processed successfully and Knowledge Graph created for folder: {result.get("folder_name", "Unknown")}',
                    'statistics': result.get('statistics', {}),
                    'iflow_file': result.get('iflow_file', ''),
                    'folder_name': result.get('folder_name', ''),
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
            else:
                # Check if it's a duplicate folder error
                error_message = result.get('error', 'Unknown error occurred')
                if 'already exists' in error_message.lower():
                    return jsonify({
                        'success': False,
                        'error': f'Folder "{folder_name}" already exists in the database. Please use a different name or clear the existing folder first.',
                        'folder_name': folder_name,
                        'error_type': 'duplicate_folder'
                    }), 409  # Conflict status code
                else:
                    return jsonify({
                        'success': False,
                        'error': error_message
                    }), 500
                
    except Exception as e:
        logger.error(f"Unexpected error in upload-base64 endpoint: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
