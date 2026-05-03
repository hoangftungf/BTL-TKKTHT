import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { chatbotService } from '../services/aiService';
import { formatPrice } from '../utils/format';

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Xin chao! Toi la tro ly AI cua shop. Toi co the giup gi cho ban?',
      products: null,
      boughtTogether: null,
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Quick action buttons
  const quickActions = [
    { text: 'Tim laptop', icon: '💻' },
    { text: 'San pham ban chay', icon: '🔥' },
    { text: 'Goi y cho toi', icon: '💡' },
    { text: 'Chinh sach doi tra', icon: '📋' },
  ];

  const handleQuickAction = (action) => {
    setInput(action);
    handleSend(action);
  };

  const handleSend = async (messageText = null) => {
    const userMessage = messageText || input.trim();
    if (!userMessage || loading) return;

    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await chatbotService.sendMessage(
        userMessage,
        conversationId
      );

      if (response.data.conversation_id) {
        setConversationId(response.data.conversation_id);
      }

      // Extract products and bought together from response
      const products = response.data.products || null;
      const boughtTogether = response.data.bought_together || null;

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.data.response,
          products: products,
          boughtTogether: boughtTogether,
          usedKG: response.data.used_knowledge_graph,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Xin loi, da co loi xay ra. Vui long thu lai sau.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Product card component for chat
  const ProductCard = ({ product }) => {
    const data = product.data || product;
    const productId = product.product_id || product.id;

    return (
      <Link
        to={`/products/${productId}`}
        onClick={() => setIsOpen(false)}
        className="flex items-center p-2 bg-white rounded-lg border border-gray-200 hover:border-blue-400 hover:shadow-sm transition-all"
      >
        <div className="w-12 h-12 bg-gray-100 rounded flex items-center justify-center text-xl">
          📦
        </div>
        <div className="ml-3 flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {data.name || `Product ${productId}`}
          </p>
          {data.price && (
            <p className="text-sm text-red-600 font-semibold">
              {formatPrice(data.price)}
            </p>
          )}
          {data.category && (
            <p className="text-xs text-gray-500">{data.category}</p>
          )}
        </div>
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </Link>
    );
  };

  // Message component
  const ChatMessage = ({ msg, index }) => {
    const isUser = msg.role === 'user';

    return (
      <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
        <div className={`max-w-[85%] ${isUser ? '' : 'space-y-2'}`}>
          {/* Avatar for assistant */}
          {!isUser && (
            <div className="flex items-center space-x-2 mb-1">
              <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white text-xs">AI</span>
              </div>
              <span className="text-xs text-gray-500">AI Assistant</span>
              {msg.usedKG && (
                <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                  + Knowledge Graph
                </span>
              )}
            </div>
          )}

          {/* Message content */}
          <div
            className={`px-4 py-2 rounded-lg ${
              isUser
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-800'
            }`}
          >
            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
          </div>

          {/* Products */}
          {msg.products && msg.products.length > 0 && (
            <div className="mt-2 space-y-2">
              <p className="text-xs text-gray-500 font-medium">San pham goi y:</p>
              <div className="space-y-2">
                {msg.products.slice(0, 3).map((product, idx) => (
                  <ProductCard key={idx} product={product} />
                ))}
              </div>
            </div>
          )}

          {/* Bought Together */}
          {msg.boughtTogether && msg.boughtTogether.length > 0 && (
            <div className="mt-2 p-2 bg-yellow-50 rounded-lg border border-yellow-200">
              <p className="text-xs text-yellow-700 font-medium mb-1">
                🛒 Thuong mua kem:
              </p>
              <div className="flex flex-wrap gap-1">
                {msg.boughtTogether.slice(0, 3).map((item, idx) => (
                  <Link
                    key={idx}
                    to={`/products/${item.product_id}`}
                    onClick={() => setIsOpen(false)}
                    className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded hover:bg-yellow-200"
                  >
                    {item.name || item.product_id}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Chat Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full shadow-lg hover:shadow-xl transition-all flex items-center justify-center z-50"
      >
        {isOpen ? (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[550px] bg-white rounded-xl shadow-2xl flex flex-col z-50 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold">AI Assistant</h3>
                <p className="text-sm text-blue-100">RAG + Knowledge Graph</p>
              </div>
              <div className="flex items-center space-x-1">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                <span className="text-xs">Online</span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          {messages.length === 1 && (
            <div className="p-3 border-b bg-gray-50">
              <p className="text-xs text-gray-500 mb-2">Goi y nhanh:</p>
              <div className="flex flex-wrap gap-2">
                {quickActions.map((action, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleQuickAction(action.text)}
                    className="text-xs bg-white border border-gray-200 px-3 py-1.5 rounded-full hover:bg-blue-50 hover:border-blue-300 transition-colors"
                  >
                    {action.icon} {action.text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, index) => (
              <ChatMessage key={index} msg={msg} index={index} />
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-xs">AI</span>
                  </div>
                  <div className="bg-gray-100 px-4 py-2 rounded-lg">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t p-3 bg-gray-50">
            <div className="flex space-x-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Nhap tin nhan..."
                className="flex-1 border border-gray-200 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={loading}
              />
              <button
                onClick={() => handleSend()}
                disabled={loading || !input.trim()}
                className="bg-gradient-to-r from-blue-600 to-purple-600 text-white w-10 h-10 rounded-full flex items-center justify-center hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Chatbot;
