import React, { useContext } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../../contexts/AuthContext';
import { hasRole } from '../../utils/auth';

/**
 * Role-based guard component to protect routes based on user roles
 *
 * @param {Object} props Component props
 * @param {Array<string>} props.requiredRoles List of roles that can access the route (e.g. ['admin', 'moderator'])
 * @param {React.ReactNode} props.children Child components to render when authorized
 * @param {string} [props.redirectTo='/'] Path to redirect when unauthorized
 * @returns {React.ReactNode} Rendered component or redirect
 */
const RoleGuard = ({ requiredRoles, children, redirectTo = '/' }) => {
  const { user, isAuthenticated, loading } = useContext(AuthContext);
  const location = useLocation();

  // If still loading auth state, render loading indicator
  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-gray-100">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // If not authenticated, redirect to login with return URL
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If user doesn't have required roles, redirect to specified path
  if (!hasAnyRole(user, requiredRoles)) {
    return <Navigate to={redirectTo} replace />;
  }

  // If authenticated and has required role, render children
  return children;
};

/**
 * Check if user has any of the required roles
 * 
 * @param {Object} user User object
 * @param {Array<string>} requiredRoles List of required roles
 * @returns {boolean} Whether user has any required role
 */
const hasAnyRole = (user, requiredRoles) => {
  if (!user || !requiredRoles || requiredRoles.length === 0) {
    return false;
  }

  // Check for admin role first (admins have access to everything)
  if (user.is_admin) {
    return true;
  }

  // Check for specific roles
  return requiredRoles.some(role => {
    switch(role) {
      case 'admin':
        return user.is_admin;
      case 'moderator':
        return user.is_moderator;
      case 'user':
        return true; // All authenticated users have 'user' role
      default:
        return false;
    }
  });
};

export default RoleGuard;