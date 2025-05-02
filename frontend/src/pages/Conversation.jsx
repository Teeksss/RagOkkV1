import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getConversation, sendMessage, updateConversation, addMessageFeedback } from '../api/conversations';
import { getDocuments } from '../api/documents';
import LoadingSpinner from '../components/common/LoadingSpinner';
import MarkdownRenderer from '../components/common/MarkdownRenderer';

const Conversation = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [conversation, setConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [streamingResponse, setStreamingResponse] = useState(false);
  const [currentInput, setCurrentInput] = useState('');
  const [error, setError] = useState(null);
  const [availableDocuments, setAvailableDocuments] = useState([]);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [showDocumentSelector, setShowDocumentSelector] = useState(false);
  const [editingTitle, setEditingTitle] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Load conversation
  useEffect(() => {
    const fetchConversation = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const result = await getConversation(id);
        
        setConversation(result);
        setMessages(result.messages || []);
        setNewTitle(result.title);
        
        // Set initially selected documents
        if (result.documents && result.documents.length > 0) {
          setSelectedDocuments(result.documents.map(doc => doc.id));
        }
      } catch (err) {
        console.error('Error loading conversation:', err);
        setError(err.message || 'Failed to load conversation');
      } finally {
        setLoading(false);
      }
    };
    
    fetchConversation();
  }, [id]);

  // Load documents
  useEffect(() => {
    if (showDocumentSelector) {
      const fetchDocuments = async () => {
        try {
          setDocumentsLoading(true);
          
          const result = await getDocuments({ limit: 100 });
          setAvailableDocuments(result.items || []);
        } catch (err) {
          console.error('Error loading documents:', err);
        } finally {
          setDocumentsLoading(false);
        }
      };
      
      fetchDocuments();
    }
  }, [showDocumentSelector]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Handle message input change
  const handleInputChange = (e) => {
    setCurrentInput(e.target.value);
  };

  // Handle sending a message
  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!currentInput.trim()) return;
    
    const messageContent = currentInput.trim();
    setCurrentInput('');
    
    // Add user message to UI immediately
    const userMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: messageContent,
      created_at: new Date().toISOString()
    };
    
    setMessages(prevMessages => [...prevMessages, userMessage]);
    
    // Create AI message placeholder with streaming content
    const aiMessageId = `temp-ai-${Date.now()}`;
    const aiMessage = {
      id: aiMessageId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      isStreaming: true
    };
    
    setMessages(prevMessages => [...prevMessages, aiMessage]);
    setStreamingResponse(true);
    
    try {
      setSendingMessage(true);
      
      // Send message to API with streaming option
      const response = await sendMessage(
        id,
        {
          content: messageContent,
          document_ids: selectedDocuments.length > 0 ? selectedDocuments : undefined
        },
        {
          onStreamChunk: (chunk) => {
            // Update streamed content
            setMessages(prevMessages => 
              prevMessages.map(msg => 
                msg.id === aiMessageId
                  ? { ...msg, content: msg.content + chunk }
                  : msg
              )
            );
          }
        }
      );
      
      // Replace temporary messages with real ones from server
      setMessages(prevMessages => 
        prevMessages.map(msg => {
          if (msg.id === userMessage.id) {
            return { ...response.user_message, feedback: {} };
          }
          if (msg.id === aiMessageId) {
            return { ...response.assistant_message, feedback: {} };
          }
          return msg;
        })
      );
      
    } catch (err) {
      console.error('Error sending message:', err);
      // Show error and keep the user message
      setMessages(prevMessages => 
        prevMessages.filter(msg => msg.id !== aiMessageId)
      );
      setError(err.message || 'Failed to send message');
    } finally {
      setSendingMessage(false);
      setStreamingResponse(false);
      scrollToBottom();
      
      // Focus input field again
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }
  };

  // Handle document selection
  const toggleDocumentSelection = (documentId) => {
    if (selectedDocuments.includes(documentId)) {
      setSelectedDocuments(selectedDocuments.filter(id => id !== documentId));
    } else {
      setSelectedDocuments([...selectedDocuments, documentId]);
    }
  };

  // Update conversation title
  const handleUpdateTitle = async () => {
    if (!newTitle.trim()) {
      setNewTitle(conversation.title || 'New Conversation');
      setEditingTitle(false);
      return;
    }
    
    if (newTitle === conversation.title) {
      setEditingTitle(false);
      return;
    }
    
    try {
      const result = await updateConversation(id, { title: newTitle });
      setConversation({ ...conversation, title: result.title });
      setEditingTitle(false);
    } catch (err) {
      console.error('Error updating title:', err);
      setError(err.message || 'Failed to update title');
    }
  };

  // Handle message feedback
  const handleMessageFeedback = async (messageId, isHelpful, feedbackText = '') => {
    try {
      await addMessageFeedback(id, messageId, {
        is_helpful: isHelpful,
        feedback_text: feedbackText
      });
      
      // Update message in state
      setMessages(prevMessages => 
        prevMessages.map(msg => 
          msg.id === messageId
            ? { 
                ...msg, 
                feedback: { 
                  ...msg.feedback, 
                  is_helpful: isHelpful,
                  feedback_text: feedbackText,
                  submitted: true
                } 
              }
            : msg
        )
      );
    } catch (err) {
      console.error('Error sending feedback:', err);
    }
  };

  // Format message timestamp
  const formatTimestamp = (dateString) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  // Get document name by ID
  const getDocumentName = (docId) => {
    if (conversation && conversation.documents) {
      const doc = conversation.documents.find(d => d.id === docId);
      return doc ? doc.filename : 'Unknown document';
    }
    
    const doc = availableDocuments.find(d => d.id === docId);
    return doc ? doc.filename : 'Unknown document';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error && !conversation) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
              <button
                onClick={() => navigate('/app/conversations')}
                className="mt-2 text-sm text-red-700 underline"
              >
                Go back to conversations
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900">Conversation not found</h3>
          <div className="mt-2">
            <button
              onClick={() => navigate('/app/conversations')}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
            >
              Go back to conversations
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-gray-200">
        <div className="flex-1 min-w-0">
          {editingTitle ? (
            <div className="flex items-center">
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-lg"
                placeholder="Conversation title"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleUpdateTitle();
                  } else if (e.key === 'Escape') {
                    setNewTitle(conversation.title);
                    setEditingTitle(false);
                  }
                }}
              />
              <button
                onClick={handleUpdateTitle}
                className="ml-2 inline-flex items-center px-2.5 py-1.5 border border-transparent text-xs font-medium rounded shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Save
              </button>
              <button
                onClick={() => {
                  setNewTitle(conversation.title);
                  setEditingTitle(false);
                }}
                className="ml-2 inline-flex items-center px-2.5 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
            </div>
          ) : (
            <h1
              className="text-2xl font-bold text-gray-900 truncate cursor-pointer hover:text-blue-600"
              onClick={() => setEditingTitle(true)}
            >
              {conversation.title || 'New Conversation'}
              <svg
                className="inline-block ml-2 h-5 w-5 text-gray-400"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
              </svg>
            </h1>
          )}
        </div>
        
        <div className="ml-4 flex items-center">
          <button
            type="button"
            onClick={() => setShowDocumentSelector(!showDocumentSelector)}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="-ml-0.5 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
            </svg>
            {selectedDocuments.length > 0 ? `${selectedDocuments.length} Document${selectedDocuments.length !== 1 ? 's' : ''}` : 'Add Documents'}
          </button>
        </div>
      </div>

      {/* Document selector */}
      {showDocumentSelector && (
        <div className="bg-gray-50 p-4 mb-4 rounded-md">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-900">Select documents to include in context</h3>
            <button
              onClick={() => setShowDocumentSelector(false)}
              className="text-gray-400 hover:text-gray-500"
            >
              <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
          
          {documentsLoading ? (
            <div className="flex justify-center items-center py-4">
              <LoadingSpinner size="small" />
            </div>
          ) : availableDocuments.length === 0 ? (
            <p className="text-sm text-gray-500">No documents available. Upload documents first.</p>
          ) : (
            <div className="max-h-60 overflow-y-auto border border-gray-200 rounded-md divide-y divide-gray-200">
              {availableDocuments.map((doc) => (
                <div key={doc.id} className="py-2 px-4">
                  <div className="flex items-center h-5">
                    <input
                      id={`document-${doc.id}`}
                      name={`document-${doc.id}`}
                      type="checkbox"
                      className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                      checked={selectedDocuments.includes(doc.id)}
                      onChange={() => toggleDocumentSelection(doc.id)}
                    />
                    <label htmlFor={`document-${doc.id}`} className="ml-3 block text-sm text-gray-700">
                      {doc.filename}
                    </label>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 mb-4 border border-gray-200 rounded-lg bg-white">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <svg className="h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No messages</h3>
            <p className="mt-1 text-sm text-gray-500">
              Start by sending a message below.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {messages.map((message, index) => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`relative max-w-xl rounded-lg px-4 py-2 ${
                  message.role === 'user' 
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {/* Message content */}
                  <div className="prose prose-sm max-w-none">
                    {message.isStreaming ? (
                      <div className="whitespace-pre-wrap">{message.content || 'Thinking...'}</div>
                    ) : (
                      <MarkdownRenderer content={message.content} />
                    )}
                  </div>
                  
                  {/* Sources/citations for AI messages */}
                  {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <details className="text-xs text-gray-500">
                        <summary className="cursor-pointer font-medium">Sources ({message.sources.length})</summary>
                        <ul className="mt-1 list-disc list-inside">
                          {message.sources.map((source, i) => (
                            <li key={i}>
                              <span className="font-medium">{getDocumentName(source.document_id)}</span>
                              {source.page && `, page ${source.page}`}
                            </li>
                          ))}
                        </ul>
                      </details>
                    </div>
                  )}
                  
                  {/* Message metadata */}
                  <div className="mt-1 flex justify-between items-center text-xs text-gray-500">
                    <span>{formatTimestamp(message.created_at)}</span>
                    
                    {/* Feedback options for AI responses */}
                    {message.role === 'assistant' && !message.isStreaming && (
                      <div className="ml-2 flex items-center">
                        {message.feedback && message.feedback.submitted ? (
                          <span className="text-xs text-green-500">
                            Feedback submitted
                          </span>
                        ) : (
                          <>
                            <button
                              onClick={() => handleMessageFeedback(message.id, true)}
                              className="p-1 rounded hover:bg-gray-200"
                              aria-label="Helpful"
                              title="Helpful"
                            >
                              <svg className="h-4 w-4 text-gray-500 hover:text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                              </svg>
                            </button>
                            <button
                              onClick={() => handleMessageFeedback(message.id, false)}
                              className="p-1 rounded hover:bg-gray-200"
                              aria-label="Not helpful"
                              title="Not helpful"
                            >
                              <svg className="h-4 w-4 text-gray-500 hover:text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.105-1.79l-.05-.025A4 4 0 0011.055 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z" />
                              </svg>
                            </button>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Message input */}
      <div className="mt-4">
        <form onSubmit={handleSendMessage}>
          <div className="flex items-start space-x-4">
            <div className="min-w-0 flex-1">
              <div className="relative">
                <textarea
                  id="message"
                  name="message"
                  rows={3}
                  className="block w-full border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 resize-none"
                  placeholder="Type your message..."
                  value={currentInput}
                  onChange={handleInputChange}
                  disabled={streamingResponse}
                  ref={inputRef}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      if (currentInput.trim() && !streamingResponse) {
                        handleSendMessage(e);
                      }
                    }
                  }}
                />
              </div>
            </div>
            <div className="flex-shrink-0">
              <button
                type="submit"
                disabled={!currentInput.trim() || streamingResponse}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {streamingResponse ? (
                  <>
                    <LoadingSpinner size="small" color="white" className="mr-2" />
                    Responding...
                  </>
                ) : (
                  <>
                    <svg className="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                    </svg>
                    Send
                  </>
                )}
              </button>
            </div>
          </div>
          
          {/* Selected documents for context */}
          {selectedDocuments.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {selectedDocuments.map(docId => (
                <span
                  key={docId}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                >
                  {getDocumentName(docId)}
                  <button
                    type="button"
                    onClick={() => toggleDocumentSelection(docId)}
                    className="ml-1.5 inline-flex items-center justify-center h-4 w-4 rounded-full bg-blue-200 text-blue-600 hover:bg-blue-300"
                  >
                    <svg className="h-2 w-2" stroke="currentColor" fill="none" viewBox="0 0 8 8">
                      <path strokeLinecap="round" strokeWidth="1.5" d="M1 1l6 6m0-6L1 7" />
                    </svg>
                  </button>
                </span>
              ))}
            </div>
          )}
          
          <p className="mt-2 text-xs text-gray-500">
            Tip: Press Enter to send, Shift+Enter for a new line
          </p>
        </form>
      </div>
    </div>
  );
};

export default Conversation;