import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import DocumentUpload from './components/DocumentUpload';
import { queryRAG, uploadDocument, listDocuments, deleteDocument } from './services/api';
import './styles/App.css';

/**
 * Main application component
 */
function App() {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="app">
      <header className="app-header">
        <h1>RAG/LLM Application</h1>
        <p>Ask questions about your documents using AI</p>
      </header>

      <div className="app-tabs">
        <button
          className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          Chat
        </button>
        <button
          className={`tab ${activeTab === 'documents' ? 'active' : ''}`}
          onClick={() => setActiveTab('documents')}
        >
          Documents
        </button>
      </div>

      <main className="app-content">
        {activeTab === 'chat' && (
          <ChatInterface onQuery={queryRAG} />
        )}
        
        {activeTab === 'documents' && (
          <DocumentUpload
            onUpload={uploadDocument}
            onList={listDocuments}
            onDelete={deleteDocument}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>RAG/LLM Application - Generic Boilerplate</p>
      </footer>
    </div>
  );
}

export default App;
