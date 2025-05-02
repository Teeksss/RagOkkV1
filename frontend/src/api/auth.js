import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get auth header with token for API requests
 * 
 * @returns {Object} Headers with Authorization
 */
export const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  
  return {};
};

/**
 * Login user
 * 
 * @param {Object} credentials User credentials
 * @param {string} credentials.username Username
 * @param {string} credentials.password Password
 * @param {boolean} credentials.remember Remember user
 * @returns {Promise<Object>} Login response with tokens
 */
export const login = async (credentials) => {
  try {
    const response = await axios.post(
      `${API_URL}/auth/login`,
      credentials
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Invalid username or password.'
    );
  }
};

/**
 * Register new user
 * 
 * @param {Object} userData User registration data
 * @param {string} userData.username Username
 * @param {string} userData.email Email
 * @param {string} userData.password Password
 * @param {string} userData.full_name Full name (optional)
 * @returns {Promise<Object>} Registration response
 */
export const register = async (userData) => {
  try {
    const response = await axios.post(
      `${API_URL}/auth/register`,
      userData
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Registration failed. Please try again.'
    );
  }
};

/**
 * Logout user
 * 
 * @returns {Promise<Object>} Logout response
 */
export const logout = async () => {
  try {
    const response = await axios.post(
      `${API_URL}/auth/logout`,
      {},
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Logout failed.'
    );
  }
};

/**
 * Refresh access token
 * 
 * @param {string} refreshToken Refresh token
 * @returns {Promise<Object>} New tokens
 */
export const refreshToken = async (refreshToken) => {
  try {
    const response = await axios.post(
      `${API_URL}/auth/refresh`,
      { refresh_token: refreshToken }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to refresh token.'
    );
  }
};

/**
 * Get current user profile
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
 * Request password reset
 * 
 * @param {string} email User email
 * @returns {Promise<Object>} Response
 */
export const requestPasswordReset = async (email) => {
  try {
    const response = await axios.post(
      `${API_URL}/auth/password-reset/request`,
      { email }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to request password reset.'
    );
  }
};

/**
 * Reset password with token
 * 
 * @param {Object} data Reset data
 * @param {string} data.token Reset token
 * @param {string} data.password New password
 * @returns {Promise<Object>} Response
 */
export const resetPassword = async (data) => {
  try {
    const response = await axios.post(
      `${API_URL}/auth/password-reset/confirm`,
      data
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to reset password.'
    );
  }
};

/**
 * Verify email with token
 * 
 * @param {string} token Verification token
 * @returns {Promise<Object>} Response
 */
export const verifyEmail = async (token) => {
  try {
    const response = await axios.post(
      `${API_URL}/auth/verify-email`,
      { token }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Email verification failed.'
    );
  }
};