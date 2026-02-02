# Getting Started with RAG/LLM Application

This guide will help you get started with the RAG/LLM application.

## What is RAG?

Retrieval-Augmented Generation (RAG) is a technique that enhances LLMs by providing them with relevant context from your documents. The system:

1. **Processes your documents** - Splits them into chunks and creates embeddings
2. **Stores embeddings** - Saves them in a vector database for fast retrieval
3. **Retrieves relevant context** - When you ask a question, it finds the most relevant chunks
4. **Generates answers** - Feeds the context to an LLM to generate accurate, grounded responses

## First Steps

### 1. Set Up Your Environment

Follow the installation instructions in the main README.md

### 2. Add Your API Key

Get an OpenAI API key from https://platform.openai.com/ and add it to `backend/.env`:

```env
OPENAI_API_KEY=sk-...
```

### 3. Start the Servers

**Local:**
```bash
# Terminal 1 - Backend
cd backend
python app.py

# Terminal 2 - Frontend
cd frontend
npm start
```

**Docker:**
```bash
docker-compose up
```

### 4. Upload Your First Document

1. Open http://localhost:3000
2. Click the "Documents" tab
3. Click "Choose File" and select a document
4. Click "Upload Document"
5. Wait for the upload to complete

### 5. Ask Your First Question

1. Click the "Chat" tab
2. Type a question about your document
3. Click "Send"
4. View the answer and sources

## Tips for Best Results

### Document Selection
- Start with well-structured documents
- Text-based formats work best (TXT, MD, PDF)
- Ensure documents have clear, readable content

### Question Formatting
- Ask specific, focused questions
- Reference topics from your documents
- Use complete sentences

### Parameter Tuning

**Temperature (0.0 - 1.0)**
- Lower (0.0 - 0.3): More focused, deterministic answers
- Medium (0.4 - 0.7): Balanced creativity and accuracy
- Higher (0.8 - 1.0): More creative, varied responses

**Max Results (1 - 10)**
- Fewer results: Faster, more focused answers
- More results: Broader context, better for complex questions

## Common Use Cases

### Knowledge Base
Upload company documentation, manuals, or wikis and create a searchable knowledge base.

### Research Assistant
Upload research papers and ask questions to extract insights and summaries.

### Document Analysis
Upload reports or articles and analyze content, extract key points, or compare information.

### Learning Tool
Upload educational materials and ask questions to reinforce learning.

## Next Steps

- Explore the API documentation at http://localhost:8000/docs
- Customize the frontend styling in `frontend/src/styles/`
- Add support for more document types in `backend/document_processor.py`
- Integrate with other LLM providers
- Deploy to production (AWS, Azure, GCP, etc.)

## Need Help?

- Check the main README.md for troubleshooting
- Review the API documentation
- Examine the code comments for implementation details
