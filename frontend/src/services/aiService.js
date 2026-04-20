import api from './api';

// AI Recommendation Service
export const recommendationService = {
  getPersonalized: (userId, limit = 10) =>
    api.get(`/recommendations/user/${userId}/?limit=${limit}`),

  getSimilar: (productId, limit = 10) =>
    api.get(`/recommendations/product/${productId}/?limit=${limit}`),

  getTrending: (limit = 10) =>
    api.get(`/recommendations/trending/?limit=${limit}`),

  recordInteraction: (data) =>
    api.post('/recommendations/interact/', data),
};

// AI Search Service
export const searchService = {
  search: (query, filters = {}, page = 1, pageSize = 20) =>
    api.post('/search/', {
      query,
      ...filters,
      page,
      page_size: pageSize,
    }),

  searchGet: (query, page = 1, pageSize = 20) =>
    api.get(`/search/?q=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}`),

  autocomplete: (query, limit = 10) =>
    api.get(`/search/autocomplete/?q=${encodeURIComponent(query)}&limit=${limit}`),
};

// AI Chatbot Service
export const chatbotService = {
  sendMessage: (message, conversationId = null, sessionId = null) =>
    api.post('/chatbot/chat/', {
      message,
      conversation_id: conversationId,
      session_id: sessionId,
    }),

  getConversation: (conversationId) =>
    api.get(`/chatbot/conversations/${conversationId}/`),

  getFAQs: (category = null) =>
    api.get(`/chatbot/faqs/${category ? `?category=${category}` : ''}`),
};

// AI Analytics Service
export const analyticsService = {
  getDashboard: (days = 30) =>
    api.get(`/analytics/dashboard/?days=${days}`),

  getSalesReport: (startDate, endDate, groupBy = 'day') =>
    api.get(`/analytics/sales/?start_date=${startDate}&end_date=${endDate}&group_by=${groupBy}`),

  getProductAnalytics: (productId = null, days = 30) =>
    api.get(`/analytics/products/${productId ? `?product_id=${productId}&` : '?'}days=${days}`),

  getPredictions: (daysAhead = 7) =>
    api.get(`/analytics/predictions/?days=${daysAhead}`),

  getCustomerSegments: () =>
    api.get('/analytics/customers/segments/'),

  getTrends: (days = 30) =>
    api.get(`/analytics/trends/?days=${days}`),

  trackProductEvent: (productId, eventType, revenue = null) =>
    api.post('/analytics/products/', {
      product_id: productId,
      event_type: eventType,
      revenue,
    }),
};

export default {
  recommendation: recommendationService,
  search: searchService,
  chatbot: chatbotService,
  analytics: analyticsService,
};
