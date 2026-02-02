import React, { useState, useEffect } from 'react';
import '../styles/DocumentUpload.css';

/**
 * Document upload component
 */
const DocumentUpload = ({ onUpload, onList, onDelete }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const docs = await onList();
      setDocuments(docs);
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  };

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
    setMessage('');
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setMessage('');

    try {
      await onUpload(selectedFile);
      setMessage('Document uploaded successfully!');
      setSelectedFile(null);
      await loadDocuments();
      
      // Clear file input
      document.getElementById('file-input').value = '';
    } catch (error) {
      console.error('Error uploading document:', error);
      setMessage('Failed to upload document. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      await onDelete(documentId);
      setMessage('Document deleted successfully!');
      await loadDocuments();
    } catch (error) {
      console.error('Error deleting document:', error);
      setMessage('Failed to delete document. Please try again.');
    }
  };

  return (
    <div className="document-upload">
      <h2>Document Management</h2>
      
      <div className="upload-section">
        <div className="file-input-wrapper">
          <input
            id="file-input"
            type="file"
            onChange={handleFileChange}
            accept=".txt,.pdf,.doc,.docx,.md"
            disabled={uploading}
          />
          {selectedFile && (
            <div className="selected-file">
              Selected: {selectedFile.name}
            </div>
          )}
        </div>
        
        <button
          onClick={handleUpload}
          disabled={!selectedFile || uploading}
          className="upload-button"
        >
          {uploading ? 'Uploading...' : 'Upload Document'}
        </button>
      </div>

      {message && (
        <div className={`message ${message.includes('success') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}

      <div className="documents-list">
        <h3>Uploaded Documents</h3>
        {documents.length === 0 ? (
          <p className="no-documents">No documents uploaded yet.</p>
        ) : (
          <ul>
            {documents.map((doc) => (
              <li key={doc.document_id} className="document-item">
                <div className="document-info">
                  <strong>{doc.filename}</strong>
                  <span className="document-meta">
                    {doc.num_chunks} chunks | {new Date(doc.created_at).toLocaleDateString()}
                  </span>
                </div>
                <button
                  onClick={() => handleDelete(doc.document_id)}
                  className="delete-button"
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default DocumentUpload;
