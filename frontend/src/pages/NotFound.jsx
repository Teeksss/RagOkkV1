import React from 'react';
import { Link } from 'react-router-dom';

const NotFound = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-9xl font-bold text-blue-600">404</h1>
          <h2 className="text-3xl font-extrabold text-gray-900 mt-4">Page not found</h2>
          <p className="mt-3 text-base text-gray-600">
            Sorry, we couldn't find the page you're looking for.
          </p>
          <div className="mt-8 space-y-3">
            <Link
              to="/app"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Go to Dashboard
            </Link>
            <div>
              <Link
                to="/login"
                className="mt-3 inline-block text-sm text-blue-600 hover:text-blue-500"
              >
                Or go back to login
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotFound;