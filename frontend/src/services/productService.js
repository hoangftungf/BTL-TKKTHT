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

  getProductReviews: async (productId) => {
    const response = await api.get(`/reviews/product/${productId}/`);
    return response.data;
  },

  getProductStats: async (productId) => {
    const response = await api.get(`/reviews/product/${productId}/stats/`);
    return response.data;
  },
};

export default productService;
