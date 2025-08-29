/**
 * Environment utility to handle process.env safely in browser
 */

// Polyfill for process.env in browser environment
if (typeof process === 'undefined') {
  window.process = {
    env: {
      NODE_ENV: 'development',
      REACT_APP_API_URL: 'http://localhost:8000'
    }
  };
}

export const getEnvVar = (key, defaultValue = '') => {
  if (typeof process !== 'undefined' && process.env) {
    return process.env[key] || defaultValue;
  }
  return defaultValue;
};

export const isDevelopment = () => {
  return getEnvVar('NODE_ENV', 'development') === 'development';
};

export const getApiUrl = () => {
  // For development, use direct backend connection
  return 'http://localhost:8000';
};
