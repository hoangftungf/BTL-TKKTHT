import api from './api';

const userService = {
  getProfile: async () => {
    const response = await api.get('/users/profile/');
    return response.data;
  },

  updateProfile: async (profileData) => {
    const response = await api.put('/users/profile/', profileData);
    return response.data;
  },

  getAddresses: async () => {
    const response = await api.get('/users/addresses/');
    return response.data;
  },

  addAddress: async (addressData) => {
    const response = await api.post('/users/addresses/', addressData);
    return response.data;
  },

  updateAddress: async (addressId, addressData) => {
    const response = await api.put(`/users/addresses/${addressId}/`, addressData);
    return response.data;
  },

  deleteAddress: async (addressId) => {
    const response = await api.delete(`/users/addresses/${addressId}/`);
    return response.data;
  },

  getWishlist: async () => {
    const response = await api.get('/users/wishlist/');
    return response.data;
  },

  addToWishlist: async (productId) => {
    const response = await api.post('/users/wishlist/', { product_id: productId });
    return response.data;
  },

  removeFromWishlist: async (productId) => {
    const response = await api.delete('/users/wishlist/', { data: { product_id: productId } });
    return response.data;
  },
};

export default userService;
