import { getAccessToken } from './services/api';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function apiFetch(endpoint, options = {}) {
  const token = getAccessToken();

  const headers = {
    ...(options.headers || {}),
    'Content-Type': 'application/json',
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  return response;
}