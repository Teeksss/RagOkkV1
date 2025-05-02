import React from 'react';
import PropTypes from 'prop-types';

/**
 * Loading spinner component with customizable size and color
 * 
 * @param {Object} props Component props
 * @param {string} props.size Size of spinner - small, medium, or large
 * @param {string} props.color Color of spinner - white, gray, or blue
 * @param {string} props.className Additional CSS classes
 * @returns {JSX.Element} Spinner component
 */
const LoadingSpinner = ({ size = 'medium', color = 'blue', className = '' }) => {
  const sizeClasses = {
    small: 'h-4 w-4',
    medium: 'h-8 w-8',
    large: 'h-12 w-12'
  };

  const colorClasses = {
    white: 'text-white',
    gray: 'text-gray-500',
    blue: 'text-blue-600'
  };

  return (
    <svg 
      className={`animate-spin ${sizeClasses[size]} ${colorClasses[color]} ${className}`} 
      xmlns="http://www.w3.org/2000/svg" 
      fill="none" 
      viewBox="0 0 24 24"
      data-testid="loading-spinner"
    >
      <circle 
        className="opacity-25" 
        cx="12" 
        cy="12" 
        r="10" 
        stroke="currentColor" 
        strokeWidth="4"
      ></circle>
      <path 
        className="opacity-75" 
        fill="currentColor" 
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </svg>
  );
};

LoadingSpinner.propTypes = {
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  color: PropTypes.oneOf(['white', 'gray', 'blue']),
  className: PropTypes.string
};

export default LoadingSpinner;