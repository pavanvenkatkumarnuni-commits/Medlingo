import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function getClientId() {
  let id = localStorage.getItem('medlingo_client_id');
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem('medlingo_client_id', id);
  }
  return id;
}

const client = axios.create({ baseURL: API_URL });

client.interceptors.request.use((config) => {
  config.headers['X-Client-Id'] = getClientId();
  return config;
});

export function apiErrorMessage(err, fallback = 'Something went wrong. Please try again.') {
  return err?.response?.data?.detail || fallback;
}

export default client;
