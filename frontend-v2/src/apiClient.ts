import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:5001/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;
