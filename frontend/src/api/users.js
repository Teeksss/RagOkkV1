import axios from 'axios';
import { getAuthHeader } from './auth';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get user profile
 * 
 * @returns {Promise<Object>} User profile data
 */
export const getUserProfile = async () => {
  try {
    const response = await axios.get(
      `${API_URL}/users/me`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch user profile.'
    );
  }
};

/**
 * Update user profile
 * 
 * @param {Object} userData User data to update
 * @param {string} userData.email Updated email
 * @param {string} userData.full_name Updated full name
 * @returns {Promise<Object>} Updated user profile
 */
export const updateProfile = async (userData) => {
  try {
    const response = await axios.patch(
      `${API_URL}/users/me`,
      userData,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to update profile.'
    );
  }
};

/**
 * Change user password
 * 
 * @param {Object} passwordData Password data
 * @param {string} passwordData.current_password Current password
 * @param {string} passwordData.new_password New password
 * @returns {Promise<Object>} Response
 */
export const changePassword = async (passwordData) => {
  try {
    const response = await axios.post(
      `${API_URL}/users/me/change-password`,
      passwordData,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to change password.'
    );
  }
};

/**
 * Get user API keys
 * 
 * @returns {Promise<Array<Object>>} List of API keys
 */
export const getUserApiKeys = async () => {
  try {
    const response = await axios.get(
      `${API_URL}/users/me/api-keys`,
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
 * Create new API key
 * 
 * @param {Object} keyData API key data
 * @param {string} keyData.name API key name
 * @param {string} keyData.expires_in Expiration period in days (optional)
 * @returns {Promise<Object>} Created API key
 */
export const createApiKey = async (keyData) => {
  try {
    const response = await axios.post(
      `${API_URL}/users/me/api-keys`,
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
 * Delete API key
 * 
 * @param {string} keyId API key ID
 * @returns {Promise<Object>} Response
 */
export const deleteApiKey = async (keyId) => {
  try {
    const response = await axios.delete(
      `${API_URL}/users/me/api-keys/${keyId}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to delete API key.'
    );
  }
};

/**
 * Admin: Get all users
 * For admin use only
 * 
 * @param {Object} params Query parameters
 * @returns {Promise<Object>} Users with pagination
 */
export const getUsers = async (params = {}) => {
  try {
    const { page = 1, limit = 20, query } = params;
    
    const queryParams = new URLSearchParams({
      page,
      limit
    });
    
    if (query) queryParams.append('query', query);
    
    const response = await axios.get(
      `${API_URL}/admin/users?${queryParams.toString()}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch users.'
    );
  }
};

/**
 * Admin: Get user by ID
 * For admin use only
 * 
 * @param {string} userId User ID
 * @returns {Promise<Object>} User data
 */
export const getUserById = async (userId) => {
  try {
    const response = await axios.get(
      `${API_URL}/admin/users/${userId}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to fetch user.'
    );
  }
};

/**
 * Admin: Update user
 * For admin use only
 * 
 * @param {string} userId User ID
 * @param {Object} userData User data to update
 * @returns {Promise<Object>} Updated user data
 */
export const updateUser = async (userId, userData) => {
  try {
    const response = await axios.patch(
      `${API_URL}/admin/users/${userId}`,
      userData,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to update user.'
    );
  }
};

/**
 * Admin: Delete user
 * For admin use only
 * 
 * @param {string} userId User ID
 * @returns {Promise<Object>} Response
 */
export const deleteUser = async (userId) => {
  try {
    const response = await axios.delete(
      `${API_URL}/admin/users/${userId}`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to delete user.'
    );
  }
};