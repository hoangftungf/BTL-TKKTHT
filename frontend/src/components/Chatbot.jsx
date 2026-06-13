import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import { addToCart } from '../store/slices/cartSlice';
import { setLoginModalOpen } from '../store/slices/uiSlice';
import { chatbotService } from '../services/aiService';
import { formatPrice } from '../utils/format';
import toast from 'react-hot-toast';
import { scaleInBounce, fadeInUp, staggerContainer, staggerItem } from '../utils/animations';

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Xin chào! Tôi là trợ lý AI của shop. Tôi có thể giúp gì cho bạn?',
      products: null,
      boughtTogether: null,
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [variantModalProduct, setVariantModalProduct] = useState(null);
  const [modalSelectedAttributes, setModalSelectedAttributes] = useState({});
  const [hasNewMessage, setHasNewMessage] = useState(false);
  const messagesEndRef = useRef(null);

  const dispatch = useDispatch();
  const { isAuthenticated } = useSelector((state) => state.auth);

  // Pulse ring when new message and chatbot closed
  useEffect(() => {
    if (!isOpen && messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg.role === 'assistant' && messages.length > 1) {
        setHasNewMessage(true);
      }
    }
  }, [messages, isOpen]);

  const getAttributeLabel = (key) => {
    const labels = {
      ram: 'RAM',
      ssd: 'SSD',
      color: 'Màu sắc',
      size: 'Kích cỡ',
      material: 'Chất liệu',
      storage: 'Dung lượng'
    };
    return labels[key.toLowerCase()] || key.charAt(0).toUpperCase() + key.slice(1);
  };

  const handleAddToCartClick = (e, p) => {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      dispatch(setLoginModalOpen(true));
      return;
    }

    const data = p.data || p;
    const variants = data.variants || [];

    if (variants.length === 0) {
      dispatch(addToCart({ productId: p.product_id || p.id, quantity: 1 }))
        .unwrap()
        .then(() => toast.success('Đã thêm vào giỏ hàng'))
        .catch((err) => toast.error(err));
    } else if (variants.length === 1) {
      dispatch(addToCart({ productId: p.product_id || p.id, quantity: 1, variantId: variants[0].id }))
        .unwrap()
        .then(() => toast.success('Đã thêm vào giỏ hàng'))
        .catch((err) => toast.error(err));
    } else {
      setVariantModalProduct(p);
      const initialVariant = variants.find(v => v.stock_quantity > 0) || variants[0];
      if (initialVariant && initialVariant.attributes) {
        setModalSelectedAttributes(initialVariant.attributes);
      } else {
        setModalSelectedAttributes({});
      }
    }
  };

  const handleConfirmAddVariantToCart = () => {
    if (!variantModalProduct) return;

    const data = variantModalProduct.data || variantModalProduct;
    const variants = data.variants || [];

    const match = variants.find(v => {
      if (!v.attributes) return false;
      return Object.entries(modalSelectedAttributes).every(([key, val]) => {
        return v.attributes[key] === val;
      });
    });

    if (!match) {
      toast.error('Vui lòng chọn đầy đủ thuộc tính sản phẩm');
      return;
    }

    if (match.stock_quantity <= 0) {
      toast.error('Biến thể này đã hết hàng');
      return;
    }

    dispatch(addToCart({
      productId: variantModalProduct.product_id || variantModalProduct.id,
      quantity: 1,
      variantId: match.id
    }))
      .unwrap()
      .then(() => {
        toast.success('Đã thêm vào giỏ hàng');
        setVariantModalProduct(null);
      })
      .catch((err) => toast.error(err));
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Quick action buttons
  const quickActions = [
    { text: 'Tìm laptop', icon: '💻' },
    { text: 'Sản phẩm bán chạy', icon: '🔥' },
    { text: 'Gợi ý cho tôi', icon: '💡' },
    { text: 'Chính sách đổi trả', icon: '📋' },
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
          content: 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại!',
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
  const ChatProductCard = ({ product }) => {
    const data = product.data || product;
    const productId = product.product_id || product.id;
    const variants = data.variants || [];
    const specs = data.specifications || {};

    let specSummary = "";
    if (variants.length > 0) {
      const colors = new Set();
      const sizes = new Set();
      variants.forEach(v => {
        if (v.attributes) {
          const color = v.attributes.color || v.attributes['Màu sắc'] || v.attributes['Màu'];
          const size = v.attributes.size || v.attributes['Kích cỡ'] || v.attributes['Size'] || v.attributes['Kích thước'];
          if (color) colors.add(color);
          if (size) sizes.add(size);
        }
      });
      const parts = [];
      if (colors.size > 0) parts.push(`Màu: ${Array.from(colors).join(', ')}`);
      if (sizes.size > 0) parts.push(`Size: ${Array.from(sizes).join(', ')}`);
      specSummary = parts.join(' | ');
    } else if (specs && Object.keys(specs).length > 0) {
      specSummary = Object.entries(specs).slice(0, 2).map(([k, v]) => `${k}: ${v}`).join(' | ');
    }

    return (
      <motion.div
        className="flex items-center p-2 bg-white rounded-lg border border-gray-200 hover:shadow-sm transition-all relative group"
        whileHover={{ scale: 1.02, y: -2 }}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Link
          to={`/products/${productId}`}
          onClick={() => setIsOpen(false)}
          className="flex flex-1 items-center min-w-0"
        >
          <div className="w-12 h-12 bg-gray-50 rounded flex items-center justify-center text-xl flex-shrink-0 border border-gray-100 overflow-hidden">
            {data.image_url ? (
              <img src={data.image_url} alt="" className="w-full h-full object-contain" />
            ) : '📦'}
          </div>
          <div className="ml-3 flex-1 min-w-0 pr-8">
            <p className="text-xs font-semibold text-gray-900 truncate">
              {data.name || `Product ${productId}`}
            </p>
            {specSummary && (
              <p className="text-[10px] text-gray-400 truncate mt-0.5">
                {specSummary}
              </p>
            )}
            {data.price && (
              <p className="text-xs text-red-500 font-bold mt-0.5">
                {formatPrice(data.price)}
              </p>
            )}
          </div>
        </Link>
        <motion.button
          onClick={(e) => handleAddToCartClick(e, product)}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-600 hover:text-white transition-all shadow-sm flex items-center justify-center"
          title="Thêm vào giỏ hàng"
          whileTap={{ scale: 0.9 }}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </motion.button>
      </motion.div>
    );
  };

  // Message component
  const ChatMessage = ({ msg, index }) => {
    const isUser = msg.role === 'user';

    return (
      <motion.div
        initial={{ opacity: 0, x: isUser ? 20 : -20, scale: 0.95 }}
        animate={{ opacity: 1, x: 0, scale: 1 }}
        transition={{ duration: 0.25, delay: index * 0.05 }}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
      >
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
            <motion.div
              className="mt-2 space-y-2"
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
            >
              <p className="text-xs text-gray-500 font-medium">Sản phẩm gợi ý:</p>
              <div className="space-y-2">
                {msg.products.slice(0, 3).map((product, idx) => (
                  <motion.div key={idx} variants={staggerItem}>
                    <ChatProductCard product={product} />
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Bought Together */}
          {msg.boughtTogether && msg.boughtTogether.length > 0 && (
            <motion.div
              className="mt-2 p-2 bg-yellow-50 rounded-lg border border-yellow-200"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <p className="text-xs text-yellow-700 font-medium mb-1">
                🛒 Thường mua kèm:
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
            </motion.div>
          )}
        </div>
      </motion.div>
    );
  };

  return (
    <>
      {/* Chat Button */}
      <motion.button
        onClick={() => { setIsOpen(!isOpen); setHasNewMessage(false); }}
        className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full shadow-lg hover:shadow-xl transition-shadow flex items-center justify-center z-50"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.9 }}
      >
        {hasNewMessage && !isOpen && (
          <motion.span
            className="absolute inset-0 rounded-full border-2 border-blue-400"
            animate={{ scale: [1, 1.3, 1], opacity: [0.6, 0, 0.6] }}
            transition={{ repeat: Infinity, duration: 2 }}
          />
        )}
        {isOpen ? (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        )}
      </motion.button>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            className="fixed bottom-24 right-6 w-96 h-[550px] bg-white rounded-xl shadow-2xl flex flex-col z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">AI Assistant</h3>
                  <p className="text-sm text-blue-100">RAG + Knowledge Graph</p>
                </div>
                <div className="flex items-center space-x-1">
                  <motion.span
                    className="w-2 h-2 bg-green-400 rounded-full"
                    animate={{ opacity: [1, 0.4, 1] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                  />
                  <span className="text-xs">Online</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            {messages.length === 1 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 border-b bg-gray-50"
              >
                <p className="text-xs text-gray-500 mb-2">Gợi ý nhanh:</p>
                <div className="flex flex-wrap gap-2">
                  {quickActions.map((action, idx) => (
                    <motion.button
                      key={idx}
                      onClick={() => handleQuickAction(action.text)}
                      className="text-xs bg-white border border-gray-200 px-3 py-1.5 rounded-full hover:bg-blue-50 hover:border-blue-300 transition-colors"
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                    >
                      {action.icon} {action.text}
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, index) => (
                <ChatMessage key={index} msg={msg} index={index} />
              ))}
              {loading && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex justify-start"
                >
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-xs">AI</span>
                    </div>
                    <div className="bg-gray-100 px-4 py-2 rounded-lg">
                      <div className="flex space-x-1">
                        {[0, 150, 300].map((delay, i) => (
                          <motion.div
                            key={i}
                            className="w-2 h-2 bg-gray-400 rounded-full"
                            animate={{ y: [0, -6, 0] }}
                            transition={{ repeat: Infinity, duration: 0.6, delay: delay / 1000 }}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.div>
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
                  placeholder="Nhập tin nhắn..."
                  className="flex-1 border border-gray-200 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={loading}
                />
                <motion.button
                  onClick={() => handleSend()}
                  disabled={loading || !input.trim()}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 text-white w-10 h-10 rounded-full flex items-center justify-center hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
                  whileTap={{ scale: 0.9 }}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </motion.button>
              </div>
            </div>

            {/* Quick Select Variant Modal Overlay inside Chatbot */}
            <AnimatePresence>
              {variantModalProduct && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 bg-black bg-opacity-40 backdrop-blur-sm z-50 flex items-end justify-center"
                >
                  <motion.div
                    initial={{ y: '100%' }}
                    animate={{ y: 0 }}
                    exit={{ y: '100%' }}
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    className="bg-white w-full rounded-t-xl p-4 shadow-2xl max-h-[75%] overflow-y-auto"
                  >
                    <div className="flex items-start justify-between border-b pb-2 mb-3">
                      <div>
                        <h4 className="text-[10px] font-bold text-gray-400 uppercase tracking-wide">Chọn phiên bản</h4>
                        <p className="text-xs font-semibold text-gray-900 line-clamp-1 mt-0.5">
                          {(variantModalProduct.data || variantModalProduct).name}
                        </p>
                      </div>
                      <button
                        onClick={() => setVariantModalProduct(null)}
                        className="text-gray-400 hover:text-gray-600 text-sm font-bold p-1"
                      >
                        ✕
                      </button>
                    </div>

                    {(() => {
                      const pData = variantModalProduct.data || variantModalProduct;
                      const variants = pData.variants || [];

                      const modalOptions = {};
                      variants.forEach(variant => {
                        if (variant.attributes && typeof variant.attributes === 'object') {
                          Object.entries(variant.attributes).forEach(([k, val]) => {
                            if (!modalOptions[k]) modalOptions[k] = new Set();
                            modalOptions[k].add(val);
                          });
                        }
                      });
                      Object.keys(modalOptions).forEach(k => {
                        modalOptions[k] = Array.from(modalOptions[k]);
                      });

                      const isModalOptionAvailable = (key, val) => {
                        return variants.some(variant => {
                          if (!variant.attributes || variant.stock_quantity <= 0 || !variant.is_active) return false;
                          if (variant.attributes[key] !== val) return false;
                          return Object.entries(modalSelectedAttributes).every(([selKey, selVal]) => {
                            if (selKey === key) return true;
                            return variant.attributes[selKey] === selVal;
                          });
                        });
                      };

                      const activeVariant = variants.find(variant => {
                        if (!variant.attributes) return false;
                        return Object.entries(modalSelectedAttributes).every(([k, val]) => {
                          return variant.attributes[k] === val;
                        });
                      });

                      const activePrice = activeVariant ? activeVariant.price : pData.price;
                      const activeStock = activeVariant ? activeVariant.stock_quantity : 0;

                      return (
                        <div className="space-y-4">
                          {Object.entries(modalOptions).map(([key, options]) => (
                            <div key={key}>
                              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-1.5">
                                {getAttributeLabel(key)}
                              </span>
                              <div className="flex flex-wrap gap-1.5">
                                {options.map((val) => {
                                  const isSelected = modalSelectedAttributes[key] === val;
                                  const isAvailable = isModalOptionAvailable(key, val);
                                  return (
                                    <motion.button
                                      key={val}
                                      disabled={!isAvailable}
                                      onClick={() => setModalSelectedAttributes(prev => ({ ...prev, [key]: val }))}
                                      className={`px-2.5 py-1 text-[11px] rounded-md border transition-all ${
                                        isSelected
                                          ? 'border-blue-500 bg-blue-50 text-blue-600 font-semibold'
                                          : isAvailable
                                          ? 'border-gray-200 bg-white text-gray-700 hover:border-blue-300'
                                          : 'border-gray-100 bg-gray-50 text-gray-300 cursor-not-allowed line-through'
                                      }`}
                                      whileTap={isAvailable ? { scale: 0.95 } : undefined}
                                    >
                                      {val}
                                    </motion.button>
                                  );
                                })}
                              </div>
                            </div>
                          ))}

                          <div className="bg-gray-50 rounded-lg p-2.5 flex items-center justify-between mt-4">
                            <div>
                              <span className="text-[9px] text-gray-400 block">Giá tiền</span>
                              <span className="text-xs font-bold text-red-500">{formatPrice(activePrice)}</span>
                            </div>
                            <div className="text-right">
                              <span className="text-[9px] text-gray-400 block">Kho hàng</span>
                              <span className={`text-[11px] font-semibold ${activeStock > 0 ? 'text-green-600' : 'text-red-500'}`}>
                                {activeStock > 0 ? `Còn ${activeStock} sản phẩm` : 'Hết hàng'}
                              </span>
                            </div>
                          </div>

                          <div className="flex gap-2 pt-2">
                            <button
                              onClick={() => setVariantModalProduct(null)}
                              className="flex-1 py-1.5 border border-gray-200 text-gray-700 text-xs font-semibold rounded-lg hover:bg-gray-50 transition-colors"
                            >
                              Hủy
                            </button>
                            <motion.button
                              disabled={!activeVariant || activeStock <= 0}
                              onClick={handleConfirmAddVariantToCart}
                              className="flex-1 py-1.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-xs font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity shadow-sm"
                              whileTap={activeVariant && activeStock > 0 ? { scale: 0.95 } : undefined}
                            >
                              Xác nhận
                            </motion.button>
                          </div>
                        </div>
                      );
                    })()}
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default Chatbot;
