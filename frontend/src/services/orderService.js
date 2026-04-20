import api from './api';

const orderService = {
  getOrders: async (params = {}) => {
    const response = await api.get('/orders/', { params });
    return response.data;
  },

  getOrderById: async (id) => {
    const response = await api.get(`/orders/${id}/`);
    return response.data;
  },

  createOrder: async (orderData) => {
    const response = await api.post('/orders/', orderData);
    return response.data;
  },

  cancelOrder: async (orderId, reason = '') => {
    const response = await api.put(`/orders/${orderId}/cancel/`, { reason });
    return response.data;
  },

  trackOrder: async (orderId) => {
    const response = await api.get(`/orders/${orderId}/track/`);
    return response.data;
  },
};

export default orderService;
