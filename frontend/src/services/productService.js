import api from './api';

const productService = {
  getProducts: async (params = {}) => {
    const response = await api.get('/products/', { params });
    return response.data;
  },

  getProductById: async (id) => {
    const response = await api.get(`/products/${id}/`);
    return response.data;
  },

  getCategories: async () => {
    const response = await api.get('/products/categories/');
    return response.data;
  },

  getProductsByCategory: async (categoryId, params = {}) => {
    const response = await api.get(`/products/category/${categoryId}/`, { params });
    return response.data;
  },

  searchProducts: async (query) => {
    const response = await api.get('/products/search/', { params: { q: query } });
    return response.data;
  },

  suggestProducts: async (query) => {
    const response = await api.get('/products/suggest/', { params: { q: query } });
    return response.data;
  },

  getProductReviews: async (productId) => {
    const response = await api.get(`/reviews/product/${productId}/`);
    return response.data;
  },

  getProductStats: async (productId) => {
    const response = await api.get(`/reviews/product/${productId}/stats/`);
    return response.data;
  },

  createProduct: async (productData) => {
    const response = await api.post('/products/', productData);
    return response.data;
  },

  updateProduct: async (id, productData) => {
    const response = await api.put(`/products/${id}/`, productData);
    return response.data;
  },

  deleteProduct: async (id) => {
    const response = await api.delete(`/products/${id}/`);
    return response.data;
  },

  createCategory: async (categoryData) => {
    const response = await api.post('/products/categories/', categoryData);
    return response.data;
  },

  updateCategory: async (id, categoryData) => {
    const response = await api.put(`/products/categories/${id}/`, categoryData);
    return response.data;
  },

  deleteCategory: async (id) => {
    const response = await api.delete(`/products/categories/${id}/`);
    return response.data;
  },
};

export default productService;
