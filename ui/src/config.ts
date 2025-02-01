// Default to localhost in development
const DEFAULT_API_URL = 'http://localhost:8080';

export const config = {
  apiUrl: process.env.NODE_ENV === 'production'
    ? (window.API_URL || DEFAULT_API_URL)  // Allow runtime configuration in production
    : DEFAULT_API_URL
};