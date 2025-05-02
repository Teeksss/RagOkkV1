import axios from 'axios';

/**
 * Configure global axios defaults and interceptors
 * 
 * @param {Function} onUnauthorized Callback to handle 401 responses
 */
export const configureAxios = (onUnauthorized) => {
  // Set base URL if available
  if (process.env.REACT_APP_API_URL) {
    axios.defaults.baseURL = process.env.REACT_APP_API_URL;
  }

  // Request interceptor
  axios.interceptors.request.use(
    (config) => {
      // Add auth token to requests if available
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor
  axios.interceptors.response.use(
    (response) => {
      return response;
    },
    async (error) => {
      const originalRequest = error.config;
      
      // Handle 401 Unauthorized errors
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        
        try {
          // Try to refresh token
          const refreshToken = localStorage.getItem('refresh_token');
          
          if (refreshToken) {
            const response = await axios.post('/auth/refresh', {
              refresh_token: refreshToken
            });
            
            // Update tokens
            localStorage.setItem('access_token', response.data.access_token);
            
            if (response.data.refresh_token) {
              localStorage.setItem('refresh_token', response.data.refresh_token);
            }
            
            // Retry original request
            originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
            return axios(originalRequest);
          } else {
            // No refresh token, handle unauthorized
            if (onUnauthorized) {
              onUnauthorized();
            }
          }
        } catch (refreshError) {
          // Refresh token failed, handle unauthorized
          if (onUnauthorized) {
            onUnauthorized();
          }
        }
      }
      
      // Extract error message from response
      let errorMessage = 'An error occurred. Please try again.';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      // Enhance error with better message
      error.userMessage = errorMessage;
      
      return Promise.reject(error);
    }
  );
};

/**
 * Handle API errors in components
 * 
 * @param {Error} error Error object
 * @param {Function} setError State setter for error message
 * @param {string} fallbackMessage Fallback error message
 */
export const handleApiError = (error, setError, fallbackMessage = 'An error occurred. Please try again.') => {
  console.error(error);
  
  if (error.userMessage) {
    setError(error.userMessage);
  } else if (error.response?.data?.detail) {
    setError(error.response.data.detail);
  } else if (error.message) {
    setError(error.message);
  } else {
    setError(fallbackMessage);
  }
};

/**
 * Create a debounced function
 * 
 * @param {Function} func The function to debounce
 * @param {number} wait Debounce wait time in milliseconds
 * @returns {Function} Debounced function
 */
export const debounce = (func, wait = 300) => {
  let timeout;
  
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * Format query parameters for API requests
 * 
 * @param {Object} params Object containing query parameters
 * @returns {string} Formatted query string
 */
export const formatQueryParams = (params) => {
  const queryParams = new URLSearchParams();
  
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach(item => queryParams.append(key, item));
      } else {
        queryParams.append(key, value);
      }
    }
  }
  
  const queryString = queryParams.toString();
  return queryString ? `?${queryString}` : '';
};