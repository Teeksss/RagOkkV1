/**
 * Authentication utility functions
 */

/**
 * Get JWT token's remaining time in seconds
 * 
 * @param {string} token JWT token
 * @returns {number} Remaining time in seconds
 */
export const getTokenRemainingTime = (token) => {
  try {
    const decoded = parseJwt(token);
    const expirationTime = decoded.exp * 1000; // Convert to milliseconds
    const currentTime = Date.now();
    return Math.max(0, Math.floor((expirationTime - currentTime) / 1000));
  } catch (error) {
    return 0;
  }
};

/**
 * Check if token needs to be refreshed
 * Typically we refresh if less than 5 minutes remaining
 * 
 * @param {string} token JWT token
 * @param {number} threshold Threshold in seconds (default: 300 = 5 minutes)
 * @returns {boolean} Whether token should be refreshed
 */
export const shouldRefreshToken = (token, threshold = 300) => {
  const remainingTime = getTokenRemainingTime(token);
  return remainingTime < threshold;
};

/**
 * Parse JWT token to get payload
 * 
 * @param {string} token JWT token
 * @returns {Object} Decoded token payload
 */
export const parseJwt = (token) => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map((c) => {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error parsing JWT:', error);
    return {};
  }
};

/**
 * Validate password strength
 * 
 * @param {string} password Password to validate
 * @returns {Object} Validation result with valid flag and message
 */
export const validatePassword = (password) => {
  // Check minimum length
  if (password.length < 8) {
    return {
      valid: false,
      message: 'Password must be at least 8 characters long'
    };
  }
  
  // Check for at least one uppercase letter
  if (!/[A-Z]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one uppercase letter'
    };
  }
  
  // Check for at least one lowercase letter
  if (!/[a-z]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one lowercase letter'
    };
  }
  
  // Check for at least one number
  if (!/[0-9]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one number'
    };
  }
  
  // Check for at least one special character
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one special character'
    };
  }
  
  return {
    valid: true,
    message: 'Password is strong'
  };
};

/**
 * Validate email format
 * 
 * @param {string} email Email to validate
 * @returns {boolean} Whether email is valid
 */
export const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate username format 
 * 
 * @param {string} username Username to validate
 * @returns {Object} Validation result with valid flag and message
 */
export const validateUsername = (username) => {
  // Check length
  if (username.length < 3) {
    return {
      valid: false,
      message: 'Username must be at least 3 characters long'
    };
  }
  
  // Check for valid characters (letters, numbers, underscores, hyphens)
  if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
    return {
      valid: false,
      message: 'Username can only contain letters, numbers, underscores and hyphens'
    };
  }
  
  return {
    valid: true,
    message: 'Username is valid'
  };
};