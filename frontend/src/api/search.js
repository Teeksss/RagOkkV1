import axios from 'axios';
import { getAuthHeader } from './auth';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Search documents and content
 * 
 * @param {Object} params Search parameters
 * @param {string} params.query Search query
 * @param {number} params.page Page number
 * @param {number} params.limit Items per page
 * @param {Array<string>} params.document_ids Document IDs to limit search to
 * @param {string} params.from_date Start date (ISO format)
 * @param {string} params.to_date End date (ISO format)
 * @returns {Promise<Object>} Search results with pagination
 */
export const search = async (params = {}) => {
  try {
    const { 
      query, 
      page = 1, 
      limit = 10, 
      document_ids, 
      from_date, 
      to_date 
    } = params;
    
    // Construct query parameters
    const queryParams = new URLSearchParams({
      query,
      page,
      limit
    });
    
    // Add optional filters
    if (document_ids && document_ids.length > 0) {
      document_ids.forEach(id => queryParams.append('document_id', id));
    }
    
    if (from_date) {
      queryParams.append('from_date', from_date);
    }
    
    if (to_date) {
      queryParams.append('to_date', to_date);
    }
    
    const response = await axios.get(
      `${API_URL}/search?${queryParams.toString()}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Search failed. Please try again.'
    );
  }
};

/**
 * Semantic search (similarity search)
 * 
 * @param {Object} params Search parameters
 * @param {string} params.text Text to search for similar content
 * @param {number} params.limit Maximum number of results
 * @param {Array<string>} params.document_ids Document IDs to limit search to
 * @returns {Promise<Array<Object>>} Search results
 */
export const semanticSearch = async (params = {}) => {
  try {
    const { text, limit = 5, document_ids } = params;
    
    // Construct request body
    const requestData = {
      text,
      limit
    };
    
    if (document_ids && document_ids.length > 0) {
      requestData.document_ids = document_ids;
    }
    
    const response = await axios.post(
      `${API_URL}/search/semantic`,
      requestData,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Semantic search failed. Please try again.'
    );
  }
};