import React, { createContext, useState, useEffect } from 'react';
import { login as apiLogin, logout as apiLogout, refreshToken, getAuthUser } from '../api/auth';
import { parseJwt, shouldRefreshToken, getTokenRemainingTime } from '../utils/auth';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [tokenRefreshInterval, setTokenRefreshInterval] = useState(null);

  // Initialize auth state from localStorage on app load
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const refreshTokenValue = localStorage.getItem('refresh_token');
        
        if (!token) {
          setLoading(false);
          return;
        }
        
        const tokenData = parseJwt(token);
        
        // Check if token is expired
        if (Date.now() >= tokenData.exp * 1000) {
          // Try to refresh token if we have a refresh token
          if (refreshTokenValue) {
            try {
              const result = await refreshToken(refreshTokenValue);
              
              // Store new tokens
              localStorage.setItem('access_token', result.access_token);
              
              if (result.refresh_token) {
                localStorage.setItem('refresh_token', result.refresh_token);
              }
              
              // Set authenticated state
              setIsAuthenticated(true);
              
              // Fetch user details
              await fetchUserDetails();
            } catch (err) {
              console.error('Failed to refresh token:', err);
              handleLogout();
            }
          } else {
            handleLogout();
          }
        } else {
          // Token is valid, set authenticated state
          setIsAuthenticated(true);
          
          // Fetch user details
          await fetchUserDetails();
        }
      } catch (err) {
        console.error('Authentication initialization error:', err);
        handleLogout();
      } finally {
        setLoading(false);
      }
    };
    
    initAuth();
    
    // Setup token refresh interval
    setupTokenRefresh();
    
    return () => {
      if (tokenRefreshInterval) {
        clearInterval(tokenRefreshInterval);
      }
    };
  }, []);

  // Setup token refresh interval
  const setupTokenRefresh = () => {
    // Clear any existing interval
    if (tokenRefreshInterval) {
      clearInterval(tokenRefreshInterval);
    }
    
    // Check token every minute
    const interval = setInterval(async () => {
      const token = localStorage.getItem('access_token');
      const refreshTokenValue = localStorage.getItem('refresh_token');
      
      if (!token || !refreshTokenValue) {
        return;
      }
      
      if (shouldRefreshToken(token)) {
        try {
          const result = await refreshToken(refreshTokenValue);
          
          // Store new tokens
          localStorage.setItem('access_token', result.access_token);
          
          if (result.refresh_token) {
            localStorage.setItem('refresh_token', result.refresh_token);
          }
          
          console.log('Token refreshed automatically');
        } catch (err) {
          console.error('Failed to refresh token:', err);
          // Don't logout on refresh failure, wait until token actually expires
        }
      }
    }, 60000); // Check every minute
    
    setTokenRefreshInterval(interval);
  };

  // Fetch current user details
  const fetchUserDetails = async () => {
    try {
      const userData = await getAuthUser();
      setUser(userData);
    } catch (err) {
      console.error('Failed to fetch user details:', err);
      handleLogout();
    }
  };

  // Login
  const login = async (credentials) => {
    setLoading(true);
    
    try {
      const result = await apiLogin(credentials);
      
      // Store tokens
      localStorage.setItem('access_token', result.access_token);
      localStorage.setItem('refresh_token', result.refresh_token);
      
      // Set authenticated state
      setIsAuthenticated(true);
      
      // Fetch user details
      await fetchUserDetails();
      
      // Setup token refresh interval
      setupTokenRefresh();
      
      return true;
    } catch (err) {
      console.error('Login error:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Logout
  const logout = async () => {
    setLoading(true);
    
    try {
      const refreshTokenValue = localStorage.getItem('refresh_token');
      
      if (refreshTokenValue) {
        await apiLogout(refreshTokenValue);
      }
    } catch (err) {
      console.error('Error during logout:', err);
    } finally {
      handleLogout();
      setLoading(false);
    }
  };

  // Handle logout (without API call)
  const handleLogout = () => {
    // Clear auth state
    setUser(null);
    setIsAuthenticated(false);
    
    // Clear tokens from localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // Clear token refresh interval
    if (tokenRefreshInterval) {
      clearInterval(tokenRefreshInterval);
      setTokenRefreshInterval(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        loading,
        login,
        logout,
        refreshUser: fetchUserDetails
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};