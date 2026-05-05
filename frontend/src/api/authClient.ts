import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const authClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

let refreshRequest: Promise<string | null> | null = null;

authClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default authClient;

authClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean };
    if (error.response?.status !== 401 || originalRequest?._retry) {
      return Promise.reject(error);
    }

    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    if (!refreshRequest) {
      refreshRequest = authClient
        .post('/auth/refresh', { refresh_token: refreshToken })
        .then((response) => {
          const nextToken = response.data?.access_token as string | undefined;
          if (!nextToken) {
            return null;
          }
          localStorage.setItem('token', nextToken);
          return nextToken;
        })
        .catch(() => {
          localStorage.removeItem('token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          return null;
        })
        .finally(() => {
          refreshRequest = null;
        });
    }

    const newToken = await refreshRequest;
    if (!newToken) {
      return Promise.reject(error);
    }

    originalRequest.headers.Authorization = `Bearer ${newToken}`;
    return authClient(originalRequest);
  },
);