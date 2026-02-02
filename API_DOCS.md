# API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, implement proper authentication and authorization.

## Endpoints

### Health Check

#### GET /

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### Query RAG System

#### POST /api/query

Ask a question to the RAG system.

**Request Body:**
```json
{
  "query": "What is the main topic of the document?",
  "max_results": 5,
  "temperature": 0.7
}
```

**Parameters:**
- `query` (string, required): The question to ask
- `max_results` (integer, optional): Number of source documents to retrieve (default: 5)
- `temperature` (float, optional): LLM temperature parameter 0.0-1.0 (default: 0.7)

**Response:**
```json
{
  "answer": "The main topic is...",
  "sources": [
    {
      "document_id": "abc123",
      "filename": "document.pdf",
      "chunk_index": 0,
      "content": "Preview of the relevant text..."
    }
  ],
  "confidence": null
}
```

---

### Upload Document

#### POST /api/documents/upload

Upload a document to be indexed.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with file field

**Supported Formats:**
- Text files (.txt)
- PDF files (.pdf)
- Word documents (.doc, .docx)
- Markdown files (.md)

**Response:**
```json
{
  "status": "success",
  "document_id": "abc123"
}
```

---

### List Documents

#### GET /api/documents

Get a list of all indexed documents.

**Response:**
```json
{
  "documents": [
    {
      "document_id": "abc123",
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "num_chunks": 10,
      "created_at": "2024-01-01T12:00:00"
    }
  ]
}
```

---

### Delete Document

#### DELETE /api/documents/{document_id}

Delete a document from the system.

**URL Parameters:**
- `document_id` (string, required): The ID of the document to delete

**Response:**
```json
{
  "status": "success"
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (resource doesn't exist)
- `500`: Internal Server Error

## Rate Limiting

Currently, there is no rate limiting. Implement rate limiting in production.

## CORS

CORS is configured to allow requests from:
- `http://localhost:3000` (development frontend)
- `http://localhost:8000` (API itself)

Modify `ALLOWED_ORIGINS` in `backend/config.py` for production.

## Interactive Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation where you can test all endpoints directly.

## Examples

### Using cURL

**Upload a document:**
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

**Query the system:**
```bash
curl -X POST "http://localhost:8000/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this document about?",
    "max_results": 5,
    "temperature": 0.7
  }'
```

**List documents:**
```bash
curl -X GET "http://localhost:8000/api/documents"
```

### Using Python

```python
import requests

# Upload a document
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/documents/upload',
        files={'file': f}
    )
    print(response.json())

# Query the system
response = requests.post(
    'http://localhost:8000/api/query',
    json={
        'query': 'What is this document about?',
        'max_results': 5,
        'temperature': 0.7
    }
)
print(response.json())
```

### Using JavaScript/Fetch

```javascript
// Upload a document
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('http://localhost:8000/api/documents/upload', {
  method: 'POST',
  body: formData
});
const uploadData = await uploadResponse.json();

// Query the system
const queryResponse = await fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'What is this document about?',
    max_results: 5,
    temperature: 0.7
  })
});
const queryData = await queryResponse.json();
```
