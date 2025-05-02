import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Get authentication token
 * @returns {string|null} Authentication token
 */
export const getToken = () => {
  return localStorage.getItem('authToken');
};

/**
 * Get authentication header
 * @returns {Object} Authentication header
 */
export const getAuthHeader = () => {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

/**
 * Login user
 * @param {string} username - Username
 * @param {string} password - Password
 * @returns {Promise<Object>} Login result with token and user data
 */
export const login = async (username, password) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);

  const response = await axios.post(`${API_URL}/auth/token`, formData);
  
  if (response.data.access_token) {
    localStorage.setItem('authToken', response.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));
  }
  
  return response.data;
};

/**
 * Register user
 * @param {Object} userData - User data
 * @returns {Promise<Object>} Registered user
 */
export const register = async (userData) => {
  const response = await axios.post(`${API_URL}/auth/register`, userData);
  return response.data;
};

/**
 * Logout user
 */
export const logout = () => {
  localStorage.removeItem('authToken');
  localStorage.removeItem('user');
};

/**
 * Get current user
 * @returns {Object|null} Current user
 */
export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;
  
  try {
    return JSON.parse(userStr);
  } catch (error) {
    console.error("Failed to parse user data:", error);
    return null;
  }
};

/**
 * Update user profile
 * @param {Object} userData - User data to update
 * @returns {Promise<Object>} Updated user
 */
export const updateUserProfile = async (userData) => {
  const response = await axios.put(
    `${API_URL}/users/me`,
    userData,
    { headers: getAuthHeader() }
  );
  
  // Update stored user data
  if (response.data) {
    localStorage.setItem('user', JSON.stringify(response.data));
  }
  
  return response.data;
};

/**
 * Change password
 * @param {string} currentPassword - Current password
 * @param {string} newPassword - New password
 * @returns {Promise<Object>} Result
 */
export const changePassword = async (currentPassword, newPassword) => {
  const response = await axios.put(
    `${API_URL}/users/me/password`,
    {
      current_password: currentPassword,
      new_password: newPassword
    },
    { headers: getAuthHeader() }
  );
  
  return response.data;
};

/**
 * Reset password request
 * @param {string} email - User email
 * @returns {Promise<Object>} Result
 */
export const resetPasswordRequest = async (email) => {
  const response = await axios.post(
    `${API_URL}/auth/reset-password`,
    { email }
  );
  
  return response.data;
};

/**
 * Check if user has role
 * @param {string} role - Role to check
 * @returns {boolean} Whether user has role
 */
export const hasRole = (role) => {
  const user = getCurrentUser();
  if (!user) return false;
  
  if (role === 'admin') {
    return user.is_admin === true;
  }
  
  if (role === 'moderator') {
    return user.is_moderator === true || user.is_admin === true;
  }
  
  // Everyone has the 'user' role if they're authenticated
  if (role === 'user') {
    return true;
  }
  
  return false;
};