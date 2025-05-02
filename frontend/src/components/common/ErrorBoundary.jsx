import React, { Component } from 'react';
import PropTypes from 'prop-types';

/**
 * Error boundary component to catch JavaScript errors in children
 * and display a fallback UI instead of crashing the app
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // You can also log the error to an error reporting service
    this.setState({ errorInfo });
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
    
    // Optional: send error to logging service
    // logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // If a custom fallback is provided, use it
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      // Default error fallback UI
      return (
        <div className="p-6 bg-white rounded-lg shadow-lg max-w-lg mx-auto my-8">
          <div className="flex items-center mb-4">
            <svg className="w-8 h-8 text-red-500 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
              />
            </svg>
            <h2 className="text-xl font-bold text-gray-800">Something went wrong</h2>
          </div>
          
          <div className="mb-4">
            <p className="text-gray-600">
              An error occurred in this application. Please try refreshing the page or contact support if the problem persists.
            </p>
          </div>
          
          {this.props.resetErrorBoundary && (
            <button
              onClick={this.props.resetErrorBoundary}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Try again
            </button>
          )}
          
          {this.props.showDetails && (
            <details className="mt-4 p-4 bg-gray-50 rounded border border-gray-200">
              <summary className="cursor-pointer text-sm text-gray-700 font-medium">
                Technical Details
              </summary>
              <div className="mt-2">
                <p className="text-sm font-mono text-red-600 whitespace-pre-wrap overflow-auto max-h-48">
                  {this.state.error && this.state.error.toString()}
                </p>
                {this.state.errorInfo && (
                  <div className="mt-2">
                    <p className="text-xs font-mono text-gray-600 whitespace-pre-wrap overflow-auto max-h-48">
                      {this.state.errorInfo.componentStack}
                    </p>
                  </div>
                )}
              </div>
            </details>
          )}
        </div>
      );
    }

    // If there's no error, render children normally
    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.node,
  resetErrorBoundary: PropTypes.func,
  showDetails: PropTypes.bool
};

ErrorBoundary.defaultProps = {
  showDetails: process.env.NODE_ENV !== 'production'
};

export default ErrorBoundary;