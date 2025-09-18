import axios from 'axios';

const apiBaseURL = import.meta.env.VITE_API_BASE_URL?.trim() || '/api';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: apiBaseURL,
  timeout: 10000,
  withCredentials: true,
});

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me'),
};

// Users API
export const usersAPI = {
  getAll: () => api.get('/users'),
  getById: (id) => api.get(`/users/${id}`),
  create: (userData) => api.post('/users', userData),
  update: (id, userData) => api.put(`/users/${id}`, userData),
  delete: (id) => api.delete(`/users/${id}`),
};

// Locations API
export const locationsAPI = {
  getAll: () => api.get('/locations'),
  getById: (id) => api.get(`/locations/${id}`),
  create: (locationData) => api.post('/locations', locationData),
  update: (id, locationData) => api.put(`/locations/${id}`, locationData),
  delete: (id) => api.delete(`/locations/${id}`),
};

// Suppliers API
export const suppliersAPI = {
  getAll: () => api.get('/suppliers'),
  getById: (id) => api.get(`/suppliers/${id}`),
  create: (supplierData) => api.post('/suppliers', supplierData),
  update: (id, supplierData) => api.put(`/suppliers/${id}`, supplierData),
  delete: (id) => api.delete(`/suppliers/${id}`),
};

// Brands API
export const brandsAPI = {
  getAll: () => api.get('/brands'),
  getById: (id) => api.get(`/brands/${id}`),
  create: (brandData) => api.post('/brands', brandData),
  update: (id, brandData) => api.put(`/brands/${id}`, brandData),
  delete: (id) => api.delete(`/brands/${id}`),
};

// Products API
export const productsAPI = {
  getAll: (params) => api.get('/products', { params }),
  getById: (id) => api.get(`/products/${id}`),
  create: (productData) => api.post('/products', productData),
  update: (id, productData) => api.put(`/products/${id}`, productData),
  delete: (id) => api.delete(`/products/${id}`),
  search: (query) => api.get(`/products/search?q=${query}`),
};

// Inventory API
export const inventoryAPI = {
  getAll: (params) => api.get('/inventory', { params }),
  getByLocation: (locationId) => api.get(`/inventory/location/${locationId}`),
  getByProduct: (productId) => api.get(`/inventory/product/${productId}`),
  adjustStock: (data) => api.post('/inventory/adjust', data),
};

// Stock Transactions API
export const stockTransactionsAPI = {
  getAll: (params) => api.get('/stock-transactions', { params }),
  getById: (id) => api.get(`/stock-transactions/${id}`),
  stockIn: (data) => api.post('/stock-transactions/stock-in', data),
  transfer: (data) => api.post('/stock-transactions/transfer', data),
  getHistory: (productId, locationId) => api.get(`/stock-transactions/history`, {
    params: { product_id: productId, location_id: locationId }
  }),
};

// Daily Count API
export const dailyCountAPI = {
  getAll: (params) => api.get('/daily-counts', { params }),
  getByDate: (date, locationId) => api.get(`/daily-counts/date/${date}`, {
    params: { location_id: locationId }
  }),
  submit: (data) => api.post('/daily-counts', data),
  update: (id, data) => api.put(`/daily-counts/${id}`, data),
};

// Reports API
export const reportsAPI = {
  getInventorySummary: (params) => api.get('/reports/inventory-summary', { params }),
  getStockMovement: (params) => api.get('/reports/stock-movement', { params }),
  getUsageSummary: (params) => api.get('/reports/usage-summary', { params }),
  getPurchaseSuggestion: (params) => api.get('/reports/purchase-suggestion', { params }),
  getLowStock: (params) => api.get('/reports/low-stock', { params }),
  export: (type, format, params) => api.get(`/reports/${type}/export`, {
    params: { ...params, format },
    responseType: 'blob'
  }),
};

// Dashboard API
export const dashboardAPI = {
  getOverview: () => api.get('/dashboard/overview'),
  getLowStockAlerts: () => api.get('/dashboard/low-stock-alerts'),
  getRecentTransactions: () => api.get('/dashboard/recent-transactions'),
  getUsageStats: (params) => api.get('/dashboard/usage-stats', { params }),
};

export default api;
