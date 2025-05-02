import axios from 'axios';
import { getAuthHeader } from './auth';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get all API keys
 * 
 * @returns {Promise<Array>} List of API keys
 */
export const getApiKeys = async () => {
  try {
    const response = await axios.get(
      `${API_URL}/api-keys`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch API keys.'
    );
  }
};

/**
 * Create a new API key
 * 
 * @param {Object} keyData API key data
 * @param {string} keyData.name API key name
 * @param {number} keyData.expires_in_days Days until expiration (0 for never)
 * @param {Array<string>} keyData.scopes Key permissions (read, write, admin)
 * @returns {Promise<Object>} Created API key
 */
export const createApiKey = async (keyData) => {
  try {
    const response = await axios.post(
      `${API_URL}/api-keys`,
      keyData,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to create API key.'
    );
  }
};

/**
 * Revoke an API key
 * 
 * @param {string} keyId API key ID to revoke
 * @returns {Promise<Object>} Response
 */
export const revokeApiKey = async (keyId) => {
  try {
    const response = await axios.delete(
      `${API_URL}/api-keys/${keyId}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to revoke API key.'
    );
  }
};