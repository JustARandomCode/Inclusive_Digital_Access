import axios from 'axios';

// VITE_API_URL is embedded at build time for production.
// For the dev server, set this in your shell or .env.local (never commit .env.local).
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT to every outgoing request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle expired / invalid tokens globally — redirect to login without silent failure
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      // Force a full page reload so React state resets cleanly to the login screen
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }),

  register: (username, password) =>
    api.post('/auth/register', { username, password }),

  verify: () =>
    api.get('/auth/verify'),
};

export const voiceAPI = {
  transcribe: (audioBlob, language = 'en') => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    // language goes as a query param only — the backend reads it from Query()
    return api.post(`/voice/transcribe?language=${language}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  simplify: (text, language = 'en') =>
    api.post('/voice/simplify', { text, language }),

  synthesize: (text, language = 'en') =>
    api.post('/voice/synthesize', { text, language }),
};

export const formsAPI = {
  // PII travels in the request body — never in URL query params
  processVoice: (text, formType) =>
    api.post('/forms/process-voice', { text, form_type: formType }),

  list: () =>
    api.get('/forms/list'),

  get: (formId) =>
    api.get(`/forms/${formId}`),

  update: (formId, formData) => {
    // Strip any MongoDB _id that crept in from list responses before sending back
    const { _id, ...clean } = formData;
    return api.put(`/forms/${formId}`, clean);
  },

  mockService: (serviceType, action, data) =>
    api.post('/forms/mock-service', {
      service_type: serviceType,
      action,
      data,
    }),
};

export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
