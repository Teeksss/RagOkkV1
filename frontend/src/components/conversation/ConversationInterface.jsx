import React, { useState, useEffect, useRef } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { searchDocuments, sendMessage, getConversationHistory } from '../../api/conversations';
import { useParams, useNavigate } from 'react-router-dom';

const ConversationInterface = ({ initialMessages = [] }) => {
  const [messages, setMessages] = useState(initialMessages);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [context, setContext] = useState([]);
  const messagesEndRef = useRef(null);
  const { conversationId } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    // Scroll to bottom when messages change
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Load conversation history if conversationId is provided
    if (conversationId) {
      loadConversationHistory();
    }
  }, [conversationId]);

  const loadConversationHistory = async () => {
    try {
      setLoading(true);
      const history = await getConversationHistory(conversationId);
      setMessages(history.messages || []);
      setError(null);
    } catch (err) {
      setError('Failed to load conversation history');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (content) => {
    if (!content.trim()) return;

    try {
      // Add user message to the list
      const userMessage = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content: content,
        timestamp: new Date().toISOString()
      };
      
      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);
      setError(null);

      // Create assistant typing indicator
      setMessages((prev) => [
        ...prev, 
        { 
          id: 'typing-indicator', 
          role: 'assistant', 
          content: '...', 
          timestamp: new Date().toISOString(),
          isLoading: true 
        }
      ]);

      // Send message to API
      const response = await sendMessage(conversationId, content);
      
      // Remove typing indicator and add real response
      setMessages((prev) => {
        const withoutTyping = prev.filter(m => m.id !== 'typing-indicator');
        return [
          ...withoutTyping,
          {
            id: response.assistant_message.id,
            role: 'assistant',
            content: response.assistant_message.content,
            timestamp: response.assistant_message.timestamp,
            metadata: response.assistant_message.metadata
          }
        ];
      });

      // Update context
      setContext(response.context || []);

      // If this is a new conversation and we got a conversation ID back
      if (!conversationId && response.assistant_message.conversation_id) {
        // Redirect to the new conversation
        navigate(`/app/conversations/${response.assistant_message.conversation_id}`);
      }

    } catch (err) {
      // Remove typing indicator
      setMessages((prev) => prev.filter(m => m.id !== 'typing-indicator'));
      
      // Add error message
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'system',
          content: 'Sorry, there was an error processing your request. Please try again.',
          timestamp: new Date().toISOString(),
          isError: true
        }
      ]);
      
      setError('Failed to send message');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleThumbsUp = async (messageId) => {
    try {
      // Create feedback in UI
      setMessages(prev => 
        prev.map(message => {
          if (message.id === messageId) {
            return {
              ...message,
              feedback: {
                ...(message.feedback || {}),
                thumbs_up: true,
                thumbs_down: false
              }
            };
          }
          return message;
        })
      );
      
      // Send feedback to API
      await submitFeedback(messageId, { thumbs_up: true, thumbs_down: false });
    } catch (err) {
      console.error('Error submitting feedback:', err);
    }
  };

  const handleThumbsDown = async (messageId) => {
    try {
      // Create feedback in UI
      setMessages(prev => 
        prev.map(message => {
          if (message.id === messageId) {
            return {
              ...message,
              feedback: {
                ...(message.feedback || {}),
                thumbs_up: false,
                thumbs_down: true
              }
            };
          }
          return message;
        })
      );
      
      // Send feedback to API
      await submitFeedback(messageId, { thumbs_up: false, thumbs_down: true });
    } catch (err) {
      console.error('Error submitting feedback:', err);
    }
  };

  const submitFeedback = async (messageId, feedback) => {
    // This would call your API to submit feedback
    // For now, it's just a placeholder
    await new Promise(resolve => setTimeout(resolve, 500));
    console.log(`Submitted feedback for message ${messageId}:`, feedback);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4">
        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
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
        
        <MessageList 
          messages={messages} 
          onThumbsUp={handleThumbsUp} 
          onThumbsDown={handleThumbsDown} 
        />
        
        <div ref={messagesEndRef} />
      </div>
      
      {context.length > 0 && (
        <div className="bg-gray-50 p-2 border-t border-gray-200">
          <div className="text-xs text-gray-500 mb-1">Sources:</div>
          <div className="flex flex-wrap gap-1">
            {context.map((source, i) => (
              <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                {source.document_id && source.title ? source.title : `Source ${i+1}`}
              </span>
            ))}
          </div>
        </div>
      )}
      
      <div className="p-4 border-t border-gray-200">
        <MessageInput 
          onSendMessage={handleSendMessage} 
          isLoading={loading} 
          disabled={loading}
        />
      </div>
    </div>
  );
};

export default ConversationInterface;