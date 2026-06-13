import api from './api';

const reviewService = {
  getProductReviews: async (productId) => {
    const response = await api.get(`/reviews/product/${productId}/`);
    return response.data;
  },

  getOrderReviews: async (orderId) => {
    const response = await api.get(`/reviews/?order_id=${orderId}`);
    return response.data;
  },

  getProductReviewStats: async (productId) => {
    const response = await api.get(`/reviews/product/${productId}/stats/`);
    return response.data;
  },

  createReview: async (reviewData) => {
    const response = await api.post('/reviews/', reviewData);
    return response.data;
  },

  replyToReview: async (reviewId, content) => {
    const response = await api.post(`/reviews/replies/${reviewId}/`, { content });
    return response.data;
  },

  adminGetReviews: async (params = {}) => {
    const response = await api.get('/reviews/admin-reviews/', { params });
    return response.data;
  },

  adminSetVisibility: async (reviewId, isVisible) => {
    const response = await api.patch(`/reviews/admin-reviews/${reviewId}/visibility/`, { is_visible: isVisible });
    return response.data;
  },
};

export default reviewService;
