import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get auth header for API requests
 * 
 * @returns {Object} Auth header object
 */
export const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  
  return token ? { Authorization: `Bearer ${token}` } : {};
};

/**
 * Login user
 * 
 * @param {Object} credentials Login credentials
 * @param {string} credentials.username Username or email
 * @param {string} credentials.password Password
 * @returns {Promise<Object>} Login response with tokens
 */
export const login = async (credentials) => {
  try {
    const response = await axios.post(
      `${API_URL}/auth/login`,
      {
        username: credentials.username,
        password: credentials.password
      }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Invalid username or password'
    );
  }
};

/**
 * Register new user
 * 
 * @param {Object} userData User registration data
 * @param {string} userData.username Username
 * @param {string} userData.email Email address
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
 * @param {string} refreshToken Refresh token
 * @returns {Promise<Object>} Logout response
 */
export const logout = async (refreshToken) => {
  try {
    const response = await axios.post(
      `${API_URL}/auth/logout/refresh`,
      { refresh_token: refreshToken }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Logout failed. Please try again.'
    );
  }
};

/**
 * Refresh access token
 * 
 * @param {string} refreshToken Refresh token
 * @returns {Promise<Object>} Token refresh response
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
      'Token refresh failed. Please login again.'
    );
  }
};

/**
 * Get authenticated user data
 * 
 * @returns {Promise<Object>} User data
 */
export const getAuthUser = async () => {
  try {
    const response = await axios.get(
      `${API_URL}/users/me`,
      { headers: getAuthHeader() }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Failed to get user data.'
    );
  }
};

/**
 * Request password reset
 * 
 * @param {string} email User email
 * @returns {Promise<Object>} Password reset request response
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
      'Password reset request failed. Please try again.'
    );
  }
};

/**
 * Reset password with token
 * 
 * @param {Object} resetData Password reset data
 * @param {string} resetData.token Reset token
 * @param {string} resetData.password New password
 * @returns {Promise<Object>} Password reset response
 */
export const resetPassword = async (resetData) => {
  try {
    const response = await axios.post(
      `${API_URL}/auth/password-reset/verify`,
      {
        token: resetData.token,
        password: resetData.password
      }
    );
    
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      'Password reset failed. Please try again.'
    );
  }
};