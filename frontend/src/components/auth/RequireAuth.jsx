import React, { useContext } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import PropTypes from 'prop-types';
import { AuthContext } from '../../contexts/AuthContext';
import LoadingSpinner from '../common/LoadingSpinner';

/**
 * Component that protects routes requiring authentication
 * 
 * @param {Object} props Component props
 * @param {React.ReactNode} props.children Child components to render when authenticated
 * @param {boolean} props.requireAdmin Whether the route requires admin privileges
 * @returns {JSX.Element} Protected route or redirect
 */
const RequireAuth = ({ children, requireAdmin = false }) => {
  const { isAuthenticated, user, loading } = useContext(AuthContext);
  const location = useLocation();

  // Show loading while checking authentication
  if (loading) {
    return (
      <div className="fixed top-0 left-0 w-full h-full flex items-center justify-center bg-gray-100">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If admin privileges are required, check if user is admin
  if (requireAdmin && (!user || !user.is_admin)) {
    // Redirect to app home if user is not an admin
    return <Navigate to="/app" replace />;
  }

  // User is authenticated and has necessary permissions, render children
  return children;
};

RequireAuth.propTypes = {
  children: PropTypes.node.isRequired,
  requireAdmin: PropTypes.bool
};

export default RequireAuth;