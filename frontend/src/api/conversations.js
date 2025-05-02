import axios from 'axios';
import { getAuthHeader } from './auth';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get conversations with pagination
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
 * @returns {Promise<Object>} Conversation data with messages
 */
export const getConversation = async (conversationId) => {
  try {
    const response = await axios.get(
      `${API_URL}/conversations/${conversationId}`,
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
 * Create new conversation
 * 
 * @param {Object} data Conversation data
 * @param {string} data.title Conversation title (optional)
 * @param {Array<string>} data.document_ids Document IDs to include (optional)
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
 * Send message in conversation
 * 
 * @param {string} conversationId Conversation ID
 * @param {Object} data Message data
 * @param {string} data.content Message content
 * @param {Array<string>} data.document_ids Document IDs to reference (optional)
 * @param {Object} options Additional options
 * @param {Function} options.onStreamChunk Callback for streaming chunks
 * @returns {Promise<Object>} Response with user and assistant messages
 */
export const sendMessage = async (conversationId, data, options = {}) => {
  try {
    // Check if streaming is supported
    const supportsStreaming = 'onStreamChunk' in options;
    
    const requestConfig = {
      headers: {
        ...getAuthHeader(),
        'Content-Type': 'application/json',
      },
    };
    
    // Add streaming support if callback provided
    if (supportsStreaming) {
      requestConfig.responseType = 'stream';
      requestConfig.onDownloadProgress = (progressEvent) => {
        const response = progressEvent.currentTarget.response;
        
        if (response) {
          try {
            // Parse streaming response chunks
            // Assuming each chunk is a complete JSON object
            const jsonChunks = response.split('\n').filter(Boolean);
            
            // Process each chunk
            jsonChunks.forEach(chunk => {
              try {
                const parsedChunk = JSON.parse(chunk);
                
                if (parsedChunk.type === 'content' && options.onStreamChunk) {
                  options.onStreamChunk(parsedChunk.content);
                }
              } catch (e) {
                console.warn('Error parsing streaming chunk:', e);
              }
            });
          } catch (e) {
            console.error('Error processing streaming response:', e);
          }
        }
      };
    }
    
    // Add streaming flag to request if supported
    const requestBody = {
      ...data,
      stream: supportsStreaming
    };
    
    const response = await axios.post(
      `${API_URL}/conversations/${conversationId}/messages`,
      requestBody,
      requestConfig
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
 * Add feedback to a message
 * 
 * @param {string} conversationId Conversation ID
 * @param {string} messageId Message ID
 * @param {Object} feedback Feedback data
 * @param {boolean} feedback.is_helpful Whether message was helpful
 * @param {string} feedback.feedback_text Additional feedback text (optional)
 * @returns {Promise<Object>} Response
 */
export const addMessageFeedback = async (conversationId, messageId, feedback) => {
  try {
    const response = await axios.post(
      `${API_URL}/conversations/${conversationId}/messages/${messageId}/feedback`,
      feedback,
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

/**
 * Get conversation history for a document
 * 
 * @param {string} documentId Document ID
 * @param {Object} params Query parameters
 * @param {number} params.page Page number
 * @param {number} params.limit Items per page
 * @returns {Promise<Object>} Conversations related to document
 */
export const getDocumentConversations = async (documentId, params = {}) => {
  try {
    const { page = 1, limit = 10 } = params;
    
    const response = await axios.get(
      `${API_URL}/documents/${documentId}/conversations?page=${page}&limit=${limit}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch document conversations.'
    );
  }
};