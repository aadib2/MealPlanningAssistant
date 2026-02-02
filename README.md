# RAG/LLM Application Boilerplate

A generic Retrieval-Augmented Generation (RAG) application built with Python (backend) and JavaScript/React (frontend). This boilerplate provides a foundation for building LLM-powered applications that can answer questions based on your own documents.

## 🚀 Features

- **Document Upload & Processing**: Upload various document formats (PDF, TXT, DOCX, MD)
- **Vector Store**: FAISS-based vector database for efficient similarity search
- **LLM Integration**: OpenAI GPT integration with configurable parameters
- **Chat Interface**: Interactive chat UI for querying your documents
- **REST API**: FastAPI backend with comprehensive endpoints
- **Modern Frontend**: React-based responsive web interface
- **Docker Support**: Easy deployment with Docker and Docker Compose

## 📁 Project Structure

```
MealPlanningAssistant/
├── backend/                 # Python FastAPI backend
│   ├── app.py              # Main FastAPI application
│   ├── rag_engine.py       # RAG engine implementation
│   ├── document_processor.py # Document processing utilities
│   ├── config.py           # Configuration management
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Backend Docker configuration
│   └── .env.example        # Environment variables template
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── ChatInterface.js
│   │   │   └── DocumentUpload.js
│   │   ├── services/       # API service layer
│   │   │   └── api.js
│   │   ├── styles/         # CSS stylesheets
│   │   ├── App.js          # Main App component
│   │   └── index.js        # Entry point
│   ├── public/             # Static files
│   ├── package.json        # Node dependencies
│   ├── Dockerfile          # Frontend Docker configuration
│   └── .env.example        # Environment variables template
└── docker-compose.yml      # Docker Compose configuration
```

## 🔧 Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key
- (Optional) Docker and Docker Compose

## 🏃 Quick Start

### Option 1: Local Setup

#### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

5. Run the backend server:
```bash
python app.py
# Or use uvicorn directly:
# uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

#### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env if you need to change the API URL
```

4. Start the development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

### Option 2: Docker Setup

1. Configure environment variables:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env and add your OPENAI_API_KEY
```

2. Build and run with Docker Compose:
```bash
docker-compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

## 📖 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### Key Endpoints

- `GET /` - Health check
- `POST /api/query` - Query the RAG system
- `POST /api/documents/upload` - Upload a document
- `GET /api/documents` - List all documents
- `DELETE /api/documents/{document_id}` - Delete a document

## 🎯 Usage

1. **Upload Documents**: Navigate to the "Documents" tab and upload your files (PDF, TXT, DOCX, MD)
2. **Ask Questions**: Switch to the "Chat" tab and ask questions about your documents
3. **Adjust Settings**: Configure temperature and max results for different response styles
4. **View Sources**: Each answer includes references to the source documents

## ⚙️ Configuration

### Backend Configuration (backend/.env)

```env
# API Settings
HOST=0.0.0.0
PORT=8000
DEBUG=True

# OpenAI API Key
OPENAI_API_KEY=your-api-key-here

# LLM Settings
LLM_MODEL=gpt-3.5-turbo

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_RETRIEVAL_DOCS=5
```

### Frontend Configuration (frontend/.env)

```env
REACT_APP_API_URL=http://localhost:8000
```

## 🔒 Security Notes

- Never commit your `.env` files with real API keys
- The `.env.example` files are templates only
- In production, use proper secret management
- Configure CORS settings appropriately for your deployment

## 🛠️ Customization

### Adding New Document Types

Edit `backend/document_processor.py` to add support for new file formats.

### Changing the LLM

Modify `backend/rag_engine.py` to use different LLM providers (e.g., Anthropic, HuggingFace).

### Changing the Vector Store

Replace FAISS with other vector databases like Pinecone, Weaviate, or Chroma in `backend/rag_engine.py`.

### Styling

Customize the appearance by editing CSS files in `frontend/src/styles/`.

## 🐛 Troubleshooting

### Backend Issues

- **Import errors**: Ensure all dependencies are installed: `pip install -r requirements.txt`
- **OpenAI errors**: Check your API key in `.env`
- **Port conflicts**: Change the PORT in `.env`

### Frontend Issues

- **Connection errors**: Verify the backend is running and REACT_APP_API_URL is correct
- **Build errors**: Delete `node_modules` and `package-lock.json`, then run `npm install` again

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Feel free to submit issues and pull requests.

## 📚 Additional Resources

- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

---

**Note**: This is a boilerplate/template project. Customize it according to your specific needs.

*Capstone Project as part of Anote Inaugural AI Academy*
