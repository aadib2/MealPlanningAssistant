/**
 * API service for communicating with the RAG/LLM backend.
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Query the RAG system
 */
export const queryRAG = async (query, maxResults = 5, temperature = 0.7) => {
  const response = await apiClient.post('/api/query', {
    query,
    max_results: maxResults,
    temperature,
  });
  return response.data;
};

/**
 * Upload a document
 */
export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await apiClient.post('/api/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * List all documents
 */
export const listDocuments = async () => {
  const response = await apiClient.get('/api/documents');
  return response.data.documents;
};

/**
 * Delete a document
 */
export const deleteDocument = async (documentId) => {
  const response = await apiClient.delete(`/api/documents/${documentId}`);
  return response.data;
};

/**
 * Health check
 */
export const healthCheck = async () => {
  const response = await apiClient.get('/');
  return response.data;
};

export default {
  queryRAG,
  uploadDocument,
  listDocuments,
  deleteDocument,
  healthCheck,
};
