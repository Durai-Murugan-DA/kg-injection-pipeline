# KG Injection Pipeline

A Flask application for uploading SAP Integration Flow (iFlow) folders and automatically generating Knowledge Graphs in Neo4j.

## Overview

This application provides an HTTP API for:
- Uploading zipped iFlow folders
- Extracting and parsing iFlow XML files
- Generating Knowledge Graphs in Neo4j
- Managing and querying the generated graphs

## Features

- **File Upload**: Accept zipped iFlow folders via HTTP POST
- **Automatic Processing**: Extract and parse iFlow XML files
- **Knowledge Graph Generation**: Create comprehensive graphs in Neo4j
- **Cloud Deployment**: Ready for SAP Cloud Foundry deployment
- **RESTful API**: Clean HTTP endpoints for integration
- **Error Handling**: Robust error handling and logging

## API Endpoints

### Health Check
```
GET /
```
Returns application status and version information.

### Upload iFlow
```
POST /upload
Content-Type: multipart/form-data
Body: file (zip file containing iFlow folder)
```
Uploads and processes an iFlow folder. Returns processing results and graph statistics.

### Database Status
```
GET /status
```
Returns current Neo4j database status and statistics.

### Clear Database
```
POST /clear
```
Clears all data from the Neo4j database.

### Export Graph
```
GET /export
```
Exports the current Knowledge Graph as a JSON file.

## Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd kg-injection-pipeline
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file:
   ```
   NEO4J_URI=neo4j://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

4. **Start Neo4j**
   Make sure Neo4j is running and accessible.

5. **Run the application**
   ```bash
   python app.py
   ```

### Cloud Foundry Deployment

1. **Set up Neo4j service**
   ```bash
   cf create-service neo4j-enterprise neo4j-service
   ```

2. **Set environment variables**
   ```bash
   cf set-env kg-injection-pipeline NEO4J_URI "neo4j://your-neo4j-host:7687"
   cf set-env kg-injection-pipeline NEO4J_USER "your-username"
   cf set-env kg-injection-pipeline NEO4J_PASSWORD "your-password"
   ```

3. **Deploy the application**
   ```bash
   cf push
   ```

## Usage

### Upload an iFlow Folder

```bash
curl -X POST \
  -F "file=@your-iflow-folder.zip" \
  http://localhost:5000/upload
```

### Check Application Status

```bash
curl http://localhost:5000/
```

### Get Database Statistics

```bash
curl http://localhost:5000/status
```

### Clear Database

```bash
curl -X POST http://localhost:5000/clear
```

### Export Graph Data

```bash
curl -O http://localhost:5000/export
```

## Integration with N8N

The application is designed to be easily integrated with N8N workflows:

1. **HTTP Request Node**: Use the `/upload` endpoint to trigger KG creation
2. **File Upload**: Send zipped iFlow folders as multipart form data
3. **Response Handling**: Process the JSON response for success/error handling

### Example N8N Workflow

1. **HTTP Request Node**:
   - Method: POST
   - URL: `https://your-app.cfapps.sap.hana.ondemand.com/upload`
   - Body: Form Data
   - File field: Upload your iFlow zip file

2. **Response Processing**:
   - Check `success` field in response
   - Handle `statistics` for graph metrics
   - Process `error` field for error handling

## File Structure

```
KG_INJECTION_PIPELINE/
├── app.py              # Main Flask application
├── kg_iflow.py         # Knowledge Graph creation logic
├── gunicorn.conf.py    # Gunicorn configuration
├── Procfile           # Cloud Foundry process definition
├── manifest.yml       # Cloud Foundry deployment manifest
├── requirements.txt   # Python dependencies
├── runtime.txt        # Python runtime version
├── .cfignore         # Cloud Foundry ignore file
└── README.md         # This file
```

## Configuration

### Environment Variables

- `NEO4J_URI`: Neo4j database URI (default: neo4j://127.0.0.1:7687)
- `NEO4J_USER`: Neo4j username (default: neo4j)
- `NEO4J_PASSWORD`: Neo4j password (default: password)
- `PORT`: Application port (default: 5000)

### Application Settings

- **Max File Size**: 100MB
- **Allowed Extensions**: .zip files only
- **Upload Directory**: `uploads/` (auto-created)
- **Logging**: INFO level with timestamp formatting

## Error Handling

The application includes comprehensive error handling:

- **File Validation**: Checks file type and size
- **Extraction Errors**: Handles corrupted or invalid zip files
- **Neo4j Connection**: Manages database connection issues
- **Processing Errors**: Graceful handling of iFlow parsing errors

## Logging

All operations are logged with timestamps:
- File uploads and extractions
- Knowledge Graph creation progress
- Error conditions and stack traces
- Database operations

## Security Considerations

- File uploads are validated for type and size
- Filenames are sanitized using `secure_filename`
- Temporary files are automatically cleaned up
- Database connections use environment variables

## Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   - Check Neo4j is running
   - Verify connection credentials
   - Check network connectivity

2. **File Upload Fails**
   - Ensure file is a valid zip file
   - Check file size (max 100MB)
   - Verify file contains .iflw files

3. **Processing Errors**
   - Check iFlow XML file validity
   - Verify file structure matches expected format
   - Review application logs for detailed errors

### Logs

View application logs:
```bash
# Local development
python app.py

# Cloud Foundry
cf logs kg-injection-pipeline --recent
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the logs for error details
2. Verify Neo4j connectivity
3. Ensure iFlow files are valid
4. Contact the development team


