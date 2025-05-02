import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { resetPassword } from '../api/auth';
import { validatePassword } from '../utils/auth';
import LoadingSpinner from '../components/common/LoadingSpinner';

const ResetPassword = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});
  
  const navigate = useNavigate();
  const location = useLocation();

  // Extract token from URL query parameters
  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const tokenParam = queryParams.get('token');
    
    if (tokenParam) {
      setToken(tokenParam);
    } else {
      setError('Password reset token is missing. Please request a new password reset link.');
    }
  }, [location]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    if (name === 'password') {
      setPassword(value);
      
      // Validate password strength
      if (value) {
        const validation = validatePassword(value);
        if (!validation.valid) {
          setValidationErrors({
            ...validationErrors,
            password: validation.message
          });
        } else {
          setValidationErrors({
            ...validationErrors,
            password: null
          });
        }
      } else {
        setValidationErrors({
          ...validationErrors,
          password: null
        });
      }
    } else if (name === 'confirmPassword') {
      setConfirmPassword(value);
      
      // Check if passwords match
      if (password && value && password !== value) {
        setValidationErrors({
          ...validationErrors,
          confirmPassword: 'Passwords do not match'
        });
      } else {
        setValidationErrors({
          ...validationErrors,
          confirmPassword: null
        });
      }
    }
    
    // Clear general error when user types
    if (error) {
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Check if we have a token
    if (!token) {
      setError('Password reset token is missing. Please request a new password reset link.');
      return;
    }
    
    // Validate password
    if (!password) {
      setError('Please enter a new password');
      return;
    }
    
    const validation = validatePassword(password);
    if (!validation.valid) {
      setError(validation.message);
      return;
    }
    
    // Check if passwords match
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      await resetPassword({
        token,
        password
      });
      
      // Show success message
      setSuccess(true);
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      console.error('Error resetting password:', err);
      setError(err.message || 'Failed to reset password. Please try again or request a new reset link.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-full flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Reset your password
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter a new password for your account
          </p>
        </div>
        
        {error && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">{error}</h3>
              </div>
            </div>
          </div>
        )}
        
        {success ? (
          <div className="rounded-md bg-green-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-green-800">Password reset successful!</h3>
                <div className="mt-2 text-sm text-green-700">
                  <p>
                    Your password has been reset successfully. You will be redirected to the login page in a moment.
                  </p>
                </div>
                <div className="mt-4">
                  <div className="-mx-2 -my-1.5 flex">
                    <Link
                      to="/login"
                      className="px-2 py-1.5 rounded-md text-sm font-medium text-green-800 hover:bg-green-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                    >
                      Go to login
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <label htmlFor="password" className="sr-only">New password</label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  className={`appearance-none rounded-t-md relative block w-full px-3 py-2 border ${
                    validationErrors.password ? 'border-red-300' : 'border-gray-300'
                  } placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                  placeholder="New password"
                  value={password}
                  onChange={handleChange}
                  disabled={loading}
                />
                {validationErrors.password && (
                  <p className="mt-2 text-sm text-red-600">{validationErrors.password}</p>
                )}
              </div>
              <div>
                <label htmlFor="confirmPassword" className="sr-only">Confirm password</label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  required
                  className={`appearance-none rounded-b-md relative block w-full px-3 py-2 border ${
                    validationErrors.confirmPassword ? 'border-red-300' : 'border-gray-300'
                  } placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
                  placeholder="Confirm password"
                  value={confirmPassword}
                  onChange={handleChange}
                  disabled={loading}
                />
                {validationErrors.confirmPassword && (
                  <p className="mt-2 text-sm text-red-600">{validationErrors.confirmPassword}</p>
                )}
              </div>
            </div>
            
            <div className="text-sm text-gray-600">
              <p>Password must contain at least:</p>
              <ul className="list-disc pl-5 mt-1">
                <li>8 characters</li>
                <li>One uppercase letter</li>
                <li>One lowercase letter</li>
                <li>One number</li>
                <li>One special character</li>
              </ul>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <LoadingSpinner size="small" color="white" className="mr-2" />
                ) : (
                  <span className="absolute left-0 inset-y-0 flex items-center pl-3">
                    <svg className="h-5 w-5 text-blue-500 group-hover:text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                    </svg>
                  </span>
                )}
                Reset password
              </button>
            </div>
            
            <div className="flex items-center justify-center">
              <div className="text-sm">
                <Link to="/login" className="font-medium text-blue-600 hover:text-blue-500">
                  Back to login
                </Link>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default ResetPassword;