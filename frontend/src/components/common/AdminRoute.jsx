import React, { useContext } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../../contexts/AuthContext';
import LoadingSpinner from './LoadingSpinner';

/**
 * Route guard that requires admin role
 * Redirects to app home if not admin
 * 
 * @param {Object} props Component props
 * @param {React.ReactNode} props.children Child components to render when authorized
 * @returns {JSX.Element} Rendered component or redirect
 */
const AdminRoute = ({ children }) => {
  const { user, isAuthenticated, loading } = useContext(AuthContext);
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-gray-100">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Redirect to app home if not admin
  if (!user?.is_admin) {
    return <Navigate to="/app" replace />;
  }

  // Render children if admin
  return children;
};

export default AdminRoute;