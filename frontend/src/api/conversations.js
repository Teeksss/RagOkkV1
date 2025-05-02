import axios from 'axios';
import { getAuthHeader } from './auth';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get all conversations
 * 
 * @param {Object} params Query parameters
 * @param {number} params.page Page number
 * @param {number} params.limit Items per page
 * @returns {Promise<Object>} Conversations with pagination
 */
export const getConversations = async (params = {}) => {
  try {
    const { page = 1, limit = 10 } = params;
    
    const response = await axios.get(
      `${API_URL}/conversations?page=${page}&limit=${limit}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch conversations.'
    );
  }
};

/**
 * Get conversation by ID
 * 
 * @param {string} conversationId Conversation ID
 * @param {Object} params Query parameters
 * @param {number} params.page Page number for messages
 * @param {number} params.limit Items per page for messages
 * @returns {Promise<Object>} Conversation with messages
 */
export const getConversation = async (conversationId, params = {}) => {
  try {
    const { page = 1, limit = 50 } = params;
    
    const response = await axios.get(
      `${API_URL}/conversations/${conversationId}?page=${page}&limit=${limit}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch conversation.'
    );
  }
};

/**
 * Create a new conversation
 * 
 * @param {Object} data Conversation data
 * @param {string} data.title Conversation title
 * @param {Array<string>} data.document_ids Document IDs to include in conversation context
 * @returns {Promise<Object>} Created conversation
 */
export const createConversation = async (data) => {
  try {
    const response = await axios.post(
      `${API_URL}/conversations`,
      data,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to create conversation.'
    );
  }
};

/**
 * Send a message in a conversation
 * 
 * @param {string} conversationId Conversation ID
 * @param {Object} data Message data
 * @param {string} data.content Message content
 * @param {Array<string>} data.document_ids Documents to include in context (optional)
 * @param {Object} options Request options
 * @param {Function} options.onStreamChunk Callback for streaming responses
 * @returns {Promise<Object>} Response message
 */
export const sendMessage = async (conversationId, data, options = {}) => {
  try {
    // Check if we need to use streaming
    if (options.onStreamChunk) {
      return sendStreamingMessage(conversationId, data, options);
    }
    
    const response = await axios.post(
      `${API_URL}/conversations/${conversationId}/messages`,
      data,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to send message.'
    );
  }
};

/**
 * Send a message with streaming response
 * 
 * @param {string} conversationId Conversation ID
 * @param {Object} data Message data
 * @param {Object} options Request options
 * @returns {Promise<Object>} Completed message
 */
const sendStreamingMessage = async (conversationId, data, options) => {
  return new Promise((resolve, reject) => {
    const { onStreamChunk } = options;
    
    // Set up event source for SSE (Server-Sent Events)
    const queryParams = new URLSearchParams({
      content: data.content,
      ...(data.document_ids ? { document_ids: data.document_ids.join(',') } : {})
    }).toString();
    
    const token = localStorage.getItem('access_token');
    const eventSource = new EventSource(
      `${API_URL}/conversations/${conversationId}/messages/stream?${queryParams}`,
      { 
        headers: { 
          'Authorization': `Bearer ${token}`
        },
        withCredentials: true
      }
    );
    
    let fullResponse = null;
    
    // Handle incoming message chunks
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'chunk') {
          // Process chunk
          onStreamChunk(data.content);
        } else if (data.type === 'end') {
          // Stream completed, return full message
          fullResponse = data.message;
          eventSource.close();
          resolve(fullResponse);
        }
      } catch (err) {
        console.error('Error parsing SSE message:', err);
      }
    };
    
    // Handle errors
    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      eventSource.close();
      reject(new Error('Stream connection failed'));
    };
  });
};

/**
 * Update conversation
 * 
 * @param {string} conversationId Conversation ID
 * @param {Object} data Update data
 * @param {string} data.title New title
 * @returns {Promise<Object>} Updated conversation
 */
export const updateConversation = async (conversationId, data) => {
  try {
    const response = await axios.patch(
      `${API_URL}/conversations/${conversationId}`,
      data,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to update conversation.'
    );
  }
};

/**
 * Delete conversation
 * 
 * @param {string} conversationId Conversation ID
 * @returns {Promise<Object>} Response
 */
export const deleteConversation = async (conversationId) => {
  try {
    const response = await axios.delete(
      `${API_URL}/conversations/${conversationId}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to delete conversation.'
    );
  }
};

/**
 * Add feedback to a message
 * 
 * @param {string} conversationId Conversation ID
 * @param {string} messageId Message ID
 * @param {Object} data Feedback data
 * @param {boolean} data.is_helpful Whether response was helpful
 * @param {string} data.feedback_text Optional feedback text
 * @returns {Promise<Object>} Response
 */
export const addMessageFeedback = async (conversationId, messageId, data) => {
  try {
    const response = await axios.post(
      `${API_URL}/conversations/${conversationId}/messages/${messageId}/feedback`,
      data,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to submit feedback.'
    );
  }
};