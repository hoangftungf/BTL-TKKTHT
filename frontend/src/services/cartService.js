import api from './api';

const cartService = {
  getCart: async () => {
    const response = await api.get('/cart/');
    return response.data;
  },

  addItem: async (productId, quantity = 1, variantId = null) => {
    const response = await api.post('/cart/items/', {
      product_id: productId,
      quantity,
      variant_id: variantId,
    });
    return response.data;
  },

  updateItem: async (itemId, quantity) => {
    const response = await api.put(`/cart/items/${itemId}/`, { quantity });
    return response.data;
  },

  removeItem: async (itemId) => {
    const response = await api.delete(`/cart/items/${itemId}/`);
    return response.data;
  },

  clearCart: async () => {
    const response = await api.delete('/cart/clear/');
    return response.data;
  },
};

export default cartService;
