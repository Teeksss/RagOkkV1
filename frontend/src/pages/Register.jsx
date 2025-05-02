import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { validatePassword, validateUsername, isValidEmail } from '../utils/auth';
import LoadingSpinner from '../components/common/LoadingSpinner';

const Register = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: ''
  });
  
  const [validationErrors, setValidationErrors] = useState({});
  const [error, setError] = useState(null);
  
  const { register, loading } = useContext(AuthContext);
  const navigate = useNavigate();
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    
    setFormData({
      ...formData,
      [name]: value
    });
    
    // Validate in real-time
    validateField(name, value);
    
    // Clear general error when user types
    if (error) {
      setError(null);
    }
  };
  
  const validateField = (name, value) => {
    const errors = { ...validationErrors };
    
    switch (name) {
      case 'username':
        if (value.trim()) {
          const usernameValidation = validateUsername(value);
          errors.username = usernameValidation.valid ? null : usernameValidation.message;
        } else {
          errors.username = null;
        }
        break;
        
      case 'email':
        if (value.trim() && !isValidEmail(value)) {
          errors.email = 'Please enter a valid email address';
        } else {
          errors.email = null;
        }
        break;
        
      case 'password':
        if (value) {
          const passwordValidation = validatePassword(value);
          errors.password = passwordValidation.valid ? null : passwordValidation.message;
          
          // Also check password confirmation if it exists
          if (formData.confirmPassword && value !== formData.confirmPassword) {
            errors.confirmPassword = 'Passwords do not match';
          } else if (formData.confirmPassword) {
            errors.confirmPassword = null;
          }
        } else {
          errors.password = null;
        }
        break;
        
      case 'confirmPassword':
        if (formData.password && value && formData.password !== value) {
          errors.confirmPassword = 'Passwords do not match';
        } else {
          errors.confirmPassword = null;
        }
        break;
        
      default:
        break;
    }
    
    setValidationErrors(errors);
  };
  
  const validateForm = () => {
    const errors = {};
    
    // Username validation
    if (!formData.username.trim()) {
      errors.username = 'Username is required';
    } else {
      const usernameValidation = validateUsername(formData.username);
      if (!usernameValidation.valid) {
        errors.username = usernameValidation.message;
      }
    }
    
    // Email validation
    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!isValidEmail(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }
    
    // Password validation
    if (!formData.password) {
      errors.password = 'Password is required';
    } else {
      const passwordValidation = validatePassword(formData.password);
      if (!passwordValidation.valid) {
        errors.password = passwordValidation.message;
      }
    }
    
    // Confirm password validation
    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!validateForm()) {
      return;
    }
    
    try {
      // Remove confirmPassword from data sent to API
      const { confirmPassword, ...registerData } = formData;
      
      await register(registerData);
      navigate('/app');
    } catch (err) {
      console.error('Registration error:', err);
      setError(err.message || 'Registration failed. Please try again.');
    }
  };
  
  return (
    <>
      <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
        Create a new account
      </h2>
      <p className="mt-2 text-center text-sm text-gray-600">
        Or{' '}
        <Link to="/login" className="font-medium text-blue-600 hover:text-blue-500">
          sign in to your existing account
        </Link>
      </p>

      {error && (
        <div className="mt-4 bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
        <div className="rounded-md shadow-sm -space-y-px">
          <div>
            <label htmlFor="username" className="sr-only">Username</label>
            <input
              id="username"
              name="username"
              type="text"
              autoComplete="username"
              required
              className={`appearance-none rounded-none relative block w-full px-3 py-2 border ${
                validationErrors.username ? 'border-red-300' : 'border-gray-300'
              } placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
              placeholder="Username"
              value={formData.username}
              onChange={handleChange}
              disabled={loading}
            />
            {validationErrors.username && (
              <p className="mt-1 text-sm text-red-600 px-3">{validationErrors.username}</p>
            )}
          </div>
          <div>
            <label htmlFor="email" className="sr-only">Email address</label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              className={`appearance-none rounded-none relative block w-full px-3 py-2 border ${
                validationErrors.email ? 'border-red-300' : 'border-gray-300'
              } placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
              placeholder="Email address"
              value={formData.email}
              onChange={handleChange}
              disabled={loading}
            />
            {validationErrors.email && (
              <p className="mt-1 text-sm text-red-600 px-3">{validationErrors.email}</p>
            )}
          </div>
          <div>
            <label htmlFor="full_name" className="sr-only">Full name (optional)</label>
            <input
              id="full_name"
              name="full_name"
              type="text"
              autoComplete="name"
              className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
              placeholder="Full name (optional)"
              value={formData.full_name}
              onChange={handleChange}
              disabled={loading}
            />
          </div>
          <div>
            <label htmlFor="password" className="sr-only">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="new-password"
              required
              className={`appearance-none rounded-none relative block w-full px-3 py-2 border ${
                validationErrors.password ? 'border-red-300' : 'border-gray-300'
              } placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              disabled={loading}
            />
            {validationErrors.password && (
              <p className="mt-1 text-sm text-red-600 px-3">{validationErrors.password}</p>
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
              className={`appearance-none rounded-none relative block w-full px-3 py-2 border ${
                validationErrors.confirmPassword ? 'border-red-300' : 'border-gray-300'
              } placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm`}
              placeholder="Confirm password"
              value={formData.confirmPassword}
              onChange={handleChange}
              disabled={loading}
            />
            {validationErrors.confirmPassword && (
              <p className="mt-1 text-sm text-red-600 px-3">{validationErrors.confirmPassword}</p>
            )}
          </div>
        </div>

        <div className="text-xs text-gray-600">
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
            disabled={loading || Object.values(validationErrors).some(error => error !== null)}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <LoadingSpinner size="small" color="white" className="mr-2" />
            ) : (
              <span className="absolute left-0 inset-y-0 flex items-center pl-3">
                <svg className="h-5 w-5 text-blue-500 group-hover:text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
              </span>
            )}
            Create Account
          </button>
        </div>
      </form>
    </>
  );
};

export default Register;