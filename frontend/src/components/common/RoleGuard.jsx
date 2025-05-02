import React, { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { AuthContext } from '../../contexts/AuthContext';

/**
 * Component for role-based access control
 * 
 * @param {Object} props - Component props
 * @param {Array} props.requiredRoles - Array of roles required to access the component
 * @param {React.ReactNode} props.children - Child components
 * @param {string} [props.redirectTo="/login"] - Redirect path if user doesn't have required roles
 * @returns {React.ReactNode} Component or redirect
 */
const RoleGuard = ({ requiredRoles, children, redirectTo = "/login" }) => {
  const { user, isAuthenticated, loading } = useContext(AuthContext);

  // If still loading auth state, render nothing or a loader
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // If not authenticated, redirect to login
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} />;
  }

  // Get user roles
  const userRoles = [];
  
  if (user.is_admin) {
    userRoles.push('admin');
  }
  
  if (user.is_moderator) {
    userRoles.push('moderator');
  }
  
  // Everyone has the 'user' role
  userRoles.push('user');

  // Check if user has any of the required roles
  const hasRequiredRole = requiredRoles.some(role => userRoles.includes(role));

  if (!hasRequiredRole) {
    // Instead of redirect, we could show an "Access Denied" message
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <h2 className="text-2xl font-bold text-red-600 mb-2">Access Denied</h2>
        <p className="text-gray-600">You don't have permission to access this page.</p>
      </div>
    );
  }

  // User has the required role, render children
  return children;
};

export default RoleGuard;