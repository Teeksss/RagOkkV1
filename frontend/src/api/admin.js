import axios from 'axios';
import { getAuthHeader } from './auth';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Fetch dashboard statistics
 * @param {string} timePeriod - Time period (24h, 7d, 30d, all)
 * @returns {Promise<Object>} Dashboard statistics
 */
export const fetchDashboardStats = async (timePeriod = '7d') => {
  const response = await axios.get(
    `${API_URL}/admin/dashboard/stats?time_period=${timePeriod}`,
    { headers: getAuthHeader() }
  );
  return response.data;
};

/**
 * Fetch active users
 * @param {string} timePeriod - Time period (24h, 7d, 30d)
 * @param {number} limit - Maximum number of users to return
 * @returns {Promise<Array>} Active users
 */
export const fetchActiveUsers = async (timePeriod = '7d', limit = 10) => {
  const response = await axios.get(
    `${API_URL}/admin/dashboard/active-users?time_period=${timePeriod}&limit=${limit}`,
    { headers: getAuthHeader() }
  );
  return response.data;
};

/**
 * Fetch popular documents
 * @param {string} timePeriod - Time period (24h, 7d, 30d)
 * @param {number} limit - Maximum number of documents to return
 * @returns {Promise<Array>} Popular documents
 */
export const fetchPopularDocuments = async (timePeriod = '7d', limit = 10) => {
  const response = await axios.get(
    `${API_URL}/admin/dashboard/popular-documents?time_period=${timePeriod}&limit=${limit}`,
    { headers: getAuthHeader() }
  );
  return response.data;
};

/**
 * Fetch query statistics
 * @param {string} timePeriod - Time period (24h, 7d, 30d)
 * @returns {Promise<Object>} Query statistics
 */
export const fetchQueryStats = async (timePeriod = '7d') => {
  const response = await axios.get(
    `${API_URL}/admin/dashboard/query-stats?time_period=${timePeriod}`,
    { headers: getAuthHeader() }
  );
  return response.data;
};

/**
 * Fetch error logs
 * @param {string} timePeriod - Time period (24h, 7d, 30d)
 * @param {number} limit - Maximum number of errors to return
 * @returns {Promise<Array>} Error logs
 */
export const fetchErrorLogs = async (timePeriod = '7d', limit = 50) => {
  const response = await axios.get(
    `${API_URL}/admin/dashboard/error-logs?time_period=${timePeriod}&limit=${limit}`,
    { headers: getAuthHeader() }
  );
  return response.data;
};

/**
 * Fetch recent feedbacks
 * @param {number} limit - Maximum number of feedbacks to return
 * @returns {Promise<Array>} Recent feedbacks
 */
export const fetchRecentFeedbacks = async (limit = 20) => {
  const response = await axios.get(
    `${API_URL}/admin/dashboard/recent-feedbacks?limit=${limit}`,
    { headers: getAuthHeader() }
  );
  return response.data;
};

/**
 * Fetch all users (admin only)
 * @param {number} skip - Number of users to skip
 * @param {number} limit - Maximum number of users to return
 * @param {string} search - Search term
 * @returns {Promise<Array>} Users
 */
export const fetchUsers = async (skip = 0, limit = 100, search = '') => {
  const searchParam = search ? `&search=${encodeURIComponent(search)}` : '';
  const response = await axios.get(
    `${API_URL}/users?skip=${skip}&limit=${limit}${searchParam}`,
    { headers: getAuthHeader() }
  );
  return response.data;
};

/**
 * Update user status (active/inactive)
 * @param {string} userId - User ID
 * @param {boolean} isActive - Whether user is active
 * @returns {Promise<Object>} Result
 */
export const updateUserStatus = async (userId, isActive) => {
  const response = await axios.put(
    `${API_URL}/users/${userId}/status`,
    { is_active: isActive },
    { headers: getAuthHeader() }
  );
  return response.data;
};

/**
 * Update user role
 * @param {string} userId - User ID
 * @param {boolean} isAdmin - Whether user is admin
 * @param {boolean} isModerator - Whether user is moderator
 * @returns {Promise<Object>} Result
 */
export const updateUserRole = async (userId, isAdmin, isModerator) => {
  const response = await axios.put(
    `${API_URL}/users/${userId}/role`,
    { is_admin: isAdmin, is_moderator: isModerator },
    { headers: getAuthHeader() }
  );
  return response.data;
};

/**
 * Fetch all API keys
 * @returns {Promise<Array>} API keys
 */
export const fetchAPIKeys = async () => {
  const response = await axios.get(
    `${API_URL}/api-keys`,
    { headers: getAuthHeader() }
  );
  return response.data;
};

/**
 * Create new API key
 * @param {Object} keyData - API key data
 * @param {string} keyData.name - Key name
 * @param {number} keyData.expires_in_days - Expiration in days
 * @param {Array<string>} keyData.scopes - API key scopes
 * @returns {Promise<Object>} Created API key
 */
export const createAPIKey = async (keyData) => {
  const response = await axios.post(
    `${API_URL}/api-keys`,
    keyData,
    { headers: getAuthHeader() }
  );
  return response.data;
};

/**
 * Revoke API key
 * @param {string} keyId - API key ID
 * @returns {Promise<Object>} Result
 */
export const revokeAPIKey = async (keyId) => {
  const response = await axios.delete(
    `${API_URL}/api-keys/${keyId}`,
    { headers: getAuthHeader() }
  );
  return response.data;
};