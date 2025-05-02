import React, { createContext, useState, useEffect } from 'react';
import { login as apiLogin, register as apiRegister, logout as apiLogout, refreshToken, getUserProfile } from '../api/auth';

// Create context
export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);
  
  // Initialize auth state from localStorage
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      
      if (token) {
        try {
          // Get user profile
          const userData = await getUserProfile();
          setUser(userData);
          setIsAuthenticated(true);
        } catch (error) {
          // If token is invalid, try to refresh
          try {
            await handleRefreshToken();
          } catch (refreshError) {
            // If refresh fails, clear auth state
            handleLogout();
          }
        }
      }
      
      setLoading(false);
    };
    
    checkAuth();
  }, []);
  
  // Set up token refresh interval
  useEffect(() => {
    if (isAuthenticated) {
      const intervalId = setInterval(() => {
        handleRefreshToken();
      }, 15 * 60 * 1000); // Refresh token every 15 minutes
      
      return () => clearInterval(intervalId);
    }
  }, [isAuthenticated]);
  
  const handleLogin = async (credentials) => {
    try {
      setLoading(true);
      setAuthError(null);
      
      const response = await apiLogin(credentials);
      
      // Store tokens
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      
      // Get user profile
      const userData = await getUserProfile();
      setUser(userData);
      setIsAuthenticated(true);
      
      return userData;
    } catch (error) {
      setAuthError(error.message || 'Login failed');
      throw error;
    } finally {
      setLoading(false);
    }
  };
  
  const handleRegister = async (userData) => {
    try {
      setLoading(true);
      setAuthError(null);
      
      const response = await apiRegister(userData);
      
      // Store tokens if registration auto-logs in
      if (response.access_token) {
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('refresh_token', response.refresh_token);
        
        // Get user profile
        const profileData = await getUserProfile();
        setUser(profileData);
        setIsAuthenticated(true);
      }
      
      return response;
    } catch (error) {
      setAuthError(error.message || 'Registration failed');
      throw error;
    } finally {
      setLoading(false);
    }
  };
  
  const handleLogout = async () => {
    try {
      setLoading(true);
      
      // Call logout API if authenticated
      if (isAuthenticated) {
        await apiLogout();
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear auth state regardless of API call result
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsAuthenticated(false);
      setLoading(false);
    }
  };
  
  const handleRefreshToken = async () => {
    try {
      const refreshTokenValue = localStorage.getItem('refresh_token');
      
      if (!refreshTokenValue) {
        throw new Error('No refresh token available');
      }
      
      const response = await refreshToken(refreshTokenValue);
      
      // Update stored tokens
      localStorage.setItem('access_token', response.access_token);
      
      // Store new refresh token if provided
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token);
      }
      
      return response;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // If refresh fails, clear auth state
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    }
  };
  
  const refreshUser = async () => {
    try {
      const userData = await getUserProfile();
      setUser(userData);
      return userData;
    } catch (error) {
      console.error('Error refreshing user data:', error);
      throw error;
    }
  };
  
  // Context value
  const contextValue = {
    user,
    isAuthenticated,
    loading,
    authError,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    refreshToken: handleRefreshToken,
    refreshUser,
  };
  
  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};