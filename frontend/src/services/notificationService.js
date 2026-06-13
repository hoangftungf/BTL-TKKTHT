import api from './api';

const notificationService = {
  getNotifications: async (params = {}) => {
    const response = await api.get('/notifications/', { params });
    return response.data;
  },

  markRead: async (data = {}) => {
    // data can be: { ids: [uuid1, uuid2] } or { all: true }
    const response = await api.post('/notifications/mark-read/', data);
    return response.data;
  },

  deleteNotification: async (id) => {
    const response = await api.delete(`/notifications/${id}/`);
    return response.data;
  },

  sendNotification: async (notificationData) => {
    // Only for admin/staff to send notification to users manually
    const response = await api.post('/notifications/send/', notificationData);
    return response.data;
  }
};

export default notificationService;
