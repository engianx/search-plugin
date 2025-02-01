// Default to localhost in development
const DEFAULT_API_URL = 'http://localhost:8080';

export const config = {
  apiUrl: import.meta.env.VITE_API_URL || // First try environment variable
    (process.env.NODE_ENV === 'production'
      ? (window.API_URL || DEFAULT_API_URL)  // Then try runtime config in production
      : DEFAULT_API_URL) // Fallback to default
};