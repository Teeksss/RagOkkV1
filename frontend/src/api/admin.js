import axios from 'axios';
import { getAuthHeader } from './auth';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get system statistics
 * Admin only
 * 
 * @returns {Promise<Object>} System stats
 */
export const getSystemStats = async () => {
  try {
    const response = await axios.get(
      `${API_URL}/admin/stats`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch system statistics.'
    );
  }
};

/**
 * Get system logs
 * Admin only
 * 
 * @param {Object} params Query parameters
 * @param {number} params.page Page number
 * @param {number} params.limit Items per page
 * @param {string} params.level Minimum log level to include
 * @returns {Promise<Object>} System logs with pagination
 */
export const getSystemLogs = async (params = {}) => {
  try {
    const { page = 1, limit = 50, level = 'info' } = params;
    
    const response = await axios.get(
      `${API_URL}/admin/logs?page=${page}&limit=${limit}&level=${level}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch system logs.'
    );
  }
};

/**
 * Get system settings
 * Admin only
 * 
 * @returns {Promise<Object>} System settings
 */
export const getSystemSettings = async () => {
  try {
    const response = await axios.get(
      `${API_URL}/admin/settings`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch system settings.'
    );
  }
};

/**
 * Update system settings
 * Admin only
 * 
 * @param {Object} settings Settings to update
 * @returns {Promise<Object>} Updated settings
 */
export const updateSystemSettings = async (settings) => {
  try {
    const response = await axios.patch(
      `${API_URL}/admin/settings`,
      settings,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to update system settings.'
    );
  }
};

/**
 * Get all API keys in the system
 * Admin only
 * 
 * @param {Object} params Query parameters
 * @returns {Promise<Object>} API keys with pagination
 */
export const getAllApiKeys = async (params = {}) => {
  try {
    const { page = 1, limit = 20 } = params;
    
    const response = await axios.get(
      `${API_URL}/admin/api-keys?page=${page}&limit=${limit}`,
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
 * Revoke an API key
 * Admin only
 * 
 * @param {string} keyId API key ID
 * @returns {Promise<Object>} Response
 */
export const revokeApiKey = async (keyId) => {
  try {
    const response = await axios.delete(
      `${API_URL}/admin/api-keys/${keyId}`,
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

/**
 * Get recent API requests
 * Admin only
 * 
 * @param {Object} params Query parameters
 * @returns {Promise<Object>} API requests with pagination
 */
export const getApiRequests = async (params = {}) => {
  try {
    const { page = 1, limit = 20, user_id, status } = params;
    
    const queryParams = new URLSearchParams({
      page,
      limit
    });
    
    if (user_id) queryParams.append('user_id', user_id);
    if (status) queryParams.append('status', status);
    
    const response = await axios.get(
      `${API_URL}/admin/api-requests?${queryParams.toString()}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch API requests.'
    );
  }
};