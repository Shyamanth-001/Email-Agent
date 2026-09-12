import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

/**
 * Fetch list of emails with optional pagination.
 * @param {number} limit 
 * @param {number} offset 
 */
export const fetchEmails = async (limit = 100, offset = 0) => {
  const response = await apiClient.get('/emails', {
    params: { limit, offset },
  });
  return response.data;
};

/**
 * Fetch single email details by ID.
 * @param {number|string} id 
 */
export const fetchEmailById = async (id) => {
  const response = await apiClient.get(`/emails/${id}`);
  return response.data;
};

/**
 * Fetch classification statistics.
 */
export const fetchStats = async () => {
  const response = await apiClient.get('/stats');
  return response.data;
};

export default apiClient;
