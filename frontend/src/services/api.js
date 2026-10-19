import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

let inMemoryAccessToken = null;
let authErrorListeners = [];

export const getAccessToken = () => inMemoryAccessToken;

export const setAccessToken = (token) => {
  inMemoryAccessToken = token;
};

export const clearAccessToken = () => {
  inMemoryAccessToken = null;
};

export const onAuthError = (listener) => {
  authErrorListeners.push(listener);
  return () => {
    authErrorListeners = authErrorListeners.filter((l) => l !== listener);
  };
};

const triggerAuthError = () => {
  clearAccessToken();
  authErrorListeners.forEach((listener) => listener());
};

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 10000,
});

// Request Interceptor: Attach Access Token
apiClient.interceptors.request.use(
  (config) => {
    if (inMemoryAccessToken) {
      config.headers.Authorization = `Bearer ${inMemoryAccessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle Token Expiration & Refresh
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (!originalRequest) {
      return Promise.reject(error);
    }

    const authEndpoints = ['/auth/login', '/auth/register', '/auth/google', '/auth/refresh'];
    const isAuthEndpoint = authEndpoints.some((endpoint) =>
      originalRequest.url?.includes(endpoint)
    );

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await apiClient.post('/auth/refresh');
        const { access_token, user } = response.data;

        setAccessToken(access_token);
        apiClient.defaults.headers.common.Authorization = `Bearer ${access_token}`;

        processQueue(null, access_token);
        isRefreshing = false;

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        isRefreshing = false;
        triggerAuthError();
        return Promise.reject(refreshErr);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API Methods
export const loginUser = async (email, password) => {
  const response = await apiClient.post('/auth/login', { email, password });
  setAccessToken(response.data.access_token);
  return response.data;
};

export const registerUser = async (email, password) => {
  const response = await apiClient.post('/auth/register', { email, password });
  setAccessToken(response.data.access_token);
  return response.data;
};

export const loginGoogle = async (credential) => {
  const response = await apiClient.post('/auth/google', { credential });
  setAccessToken(response.data.access_token);
  return response.data;
};

export const loginGoogleCode = async (code) => {
  const response = await apiClient.post('/auth/google/code', { code });
  setAccessToken(response.data.access_token);
  return response.data;
};

export const connectGmailToken = async (gmailRefreshToken, code) => {
  const params = code ? { code } : {};
  const body = gmailRefreshToken ? { gmail_refresh_token: gmailRefreshToken } : {};
  const response = await apiClient.post('/auth/connect-gmail', body, { params });
  return response.data;
};

export const refreshAuthToken = async () => {
  const response = await apiClient.post('/auth/refresh');
  setAccessToken(response.data.access_token);
  return response.data;
};

export const logoutUser = async () => {
  try {
    await apiClient.post('/auth/logout');
  } catch (err) {
    console.error('Logout error:', err);
  } finally {
    clearAccessToken();
  }
};

export const fetchMe = async () => {
  const response = await apiClient.get('/auth/me');
  return response.data;
};

// Data API Methods
export const fetchEmails = async (limit = 100, offset = 0) => {
  const response = await apiClient.get('/emails', {
    params: { limit, offset },
  });
  return response.data;
};

export const fetchEmailById = async (id) => {
  const response = await apiClient.get(`/emails/${id}`);
  return response.data;
};

export const fetchStats = async () => {
  const response = await apiClient.get('/stats');
  return response.data;
};

export default apiClient;
