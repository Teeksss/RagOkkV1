import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import { configureAxios } from './utils/apiUtils';
import ErrorBoundary from './components/common/ErrorBoundary';

// Configure axios interceptors
configureAxios(() => {
  // Handle unauthorized (401) errors - clear auth and redirect to login
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.location.href = '/login';
});

ReactDOM.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
  document.getElementById('root')
);

// Enable hot module replacement for development
if (module.hot) {
  module.hot.accept();
}