import api from './api';

const paymentService = {
  createMoMoPayment: async (orderId, amount, returnUrl) => {
    const response = await api.post('/payments/momo/', {
      order_id: orderId,
      amount,
      return_url: returnUrl,
    });
    return response.data;
  },

  createVNPayPayment: async (orderId, amount, returnUrl) => {
    const response = await api.post('/payments/vnpay/', {
      order_id: orderId,
      amount,
      return_url: returnUrl,
    });
    return response.data;
  },

  createCODPayment: async (orderId, amount) => {
    const response = await api.post('/payments/cod/', {
      order_id: orderId,
      amount,
    });
    return response.data;
  },

  getPaymentStatus: async (orderId) => {
    const response = await api.get(`/payments/${orderId}/status/`);
    return response.data;
  },
};

export default paymentService;
