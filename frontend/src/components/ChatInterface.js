import React, { useState } from 'react';
import '../styles/ChatInterface.css';

/**
 * Chat interface component for querying the RAG system
 */
const ChatInterface = ({ onQuery }) => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [temperature, setTemperature] = useState(0.7);
  const [maxResults, setMaxResults] = useState(5);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) return;

    // Add user message
    const userMessage = { role: 'user', content: query };
    setMessages(prev => [...prev, userMessage]);
    
    setLoading(true);
    setQuery('');

    try {
      const response = await onQuery(query, maxResults, temperature);
      
      // Add assistant message
      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error querying RAG:', error);
      const errorMessage = {
        role: 'error',
        content: 'Failed to get response. Please try again.',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>RAG/LLM Chat</h2>
        <div className="chat-settings">
          <label>
            Temperature:
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
            />
            <span>{temperature}</span>
          </label>
          <label>
            Max Results:
            <input
              type="number"
              min="1"
              max="10"
              value={maxResults}
              onChange={(e) => setMaxResults(parseInt(e.target.value))}
            />
          </label>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-placeholder">
            <p>Ask me anything about your uploaded documents!</p>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="message-content">
              {message.content}
            </div>
            {message.sources && message.sources.length > 0 && (
              <div className="message-sources">
                <strong>Sources:</strong>
                {message.sources.map((source, idx) => (
                  <div key={idx} className="source">
                    <span className="source-filename">{source.filename}</span>
                    <p className="source-preview">{source.content}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        
        {loading && (
          <div className="message assistant loading">
            <div className="message-content">Thinking...</div>
          </div>
        )}
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !query.trim()}>
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;
