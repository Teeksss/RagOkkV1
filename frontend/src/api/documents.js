import axios from 'axios';
import { getAuthHeader } from './auth';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get documents list with pagination
 * 
 * @param {Object} params Query parameters
 * @param {number} params.page Page number
 * @param {number} params.limit Items per page
 * @param {string} params.sort Sort field
 * @param {string} params.order Sort order (asc/desc)
 * @param {string} params.query Search query
 * @param {Array<string>} params.tags Filter by tags
 * @returns {Promise<Object>} Documents with pagination
 */
export const getDocuments = async (params = {}) => {
  try {
    const { 
      page = 1, 
      limit = 10,
      sort = 'created_at',
      order = 'desc',
      query = '',
      tags = []
    } = params;
    
    // Construct query parameters
    const queryParams = new URLSearchParams({
      page,
      limit,
      sort,
      order
    });
    
    // Add optional filters
    if (query) {
      queryParams.append('query', query);
    }
    
    if (tags && tags.length > 0) {
      tags.forEach(tag => queryParams.append('tag', tag));
    }
    
    const response = await axios.get(
      `${API_URL}/documents?${queryParams.toString()}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch documents.'
    );
  }
};

/**
 * Get document by ID
 * 
 * @param {string} documentId Document ID
 * @returns {Promise<Object>} Document data
 */
export const getDocument = async (documentId) => {
  try {
    const response = await axios.get(
      `${API_URL}/documents/${documentId}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch document.'
    );
  }
};

/**
 * Get document chunks
 * 
 * @param {string} documentId Document ID
 * @param {number} page Page number
 * @param {number} limit Items per page
 * @returns {Promise<Object>} Document chunks with pagination
 */
export const getDocumentChunks = async (documentId, page = 1, limit = 10) => {
  try {
    const response = await axios.get(
      `${API_URL}/documents/${documentId}/chunks?page=${page}&limit=${limit}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch document chunks.'
    );
  }
};

/**
 * Upload document
 * 
 * @param {File} file File to upload
 * @param {Object} metadata Additional metadata
 * @param {Array<string>} metadata.tags Document tags
 * @param {Function} onProgress Progress callback
 * @returns {Promise<Object>} Uploaded document
 */
export const uploadDocument = async (file, metadata = {}, onProgress) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    // Add tags if provided
    if (metadata.tags && metadata.tags.length > 0) {
      metadata.tags.forEach(tag => {
        formData.append('tags', tag);
      });
    }
    
    const config = {
      headers: {
        ...getAuthHeader(),
        'Content-Type': 'multipart/form-data'
      }
    };
    
    // Add progress tracking if callback provided
    if (onProgress) {
      config.onUploadProgress = (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      };
    }
    
    const response = await axios.post(
      `${API_URL}/documents/upload`,
      formData,
      config
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to upload document.'
    );
  }
};

/**
 * Delete document
 * 
 * @param {string} documentId Document ID
 * @returns {Promise<Object>} Response
 */
export const deleteDocument = async (documentId) => {
  try {
    const response = await axios.delete(
      `${API_URL}/documents/${documentId}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to delete document.'
    );
  }
};

/**
 * Update document metadata
 * 
 * @param {string} documentId Document ID
 * @param {Object} metadata Metadata to update
 * @param {Array<string>} metadata.tags Document tags
 * @returns {Promise<Object>} Updated document
 */
export const updateDocumentMetadata = async (documentId, metadata) => {
  try {
    const response = await axios.patch(
      `${API_URL}/documents/${documentId}`,
      metadata,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to update document metadata.'
    );
  }
};

/**
 * Download document
 * 
 * @param {string} documentId Document ID
 * @returns {Promise<Blob>} Document file blob
 */
export const downloadDocument = async (documentId) => {
  try {
    const response = await axios.get(
      `${API_URL}/documents/${documentId}/download`,
      { 
        headers: getAuthHeader(),
        responseType: 'blob' 
      }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to download document.'
    );
  }
};

/**
 * Get document tags
 * Returns all unique tags used across all documents
 * 
 * @returns {Promise<Array<string>>} List of document tags
 */
export const getDocumentTags = async () => {
  try {
    const response = await axios.get(
      `${API_URL}/documents/tags`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch document tags.'
    );
  }
};