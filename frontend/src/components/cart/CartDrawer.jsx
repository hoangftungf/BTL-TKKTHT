import { useEffect, useRef, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Plus, Minus, Trash2, ShoppingBag } from 'lucide-react';
import { fetchCart, updateCartItem, removeCartItem } from '../../store/slices/cartSlice';
import { setCartDrawerOpen } from '../../store/slices/uiSlice';
import toast from 'react-hot-toast';

const CartDrawer = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const drawerRef = useRef(null);
  const [removingIds, setRemovingIds] = useState(new Set());

  const { cartDrawerOpen } = useSelector((state) => state.ui);
  const { items, totalAmount, loading } = useSelector((state) => state.cart);
  const { isAuthenticated } = useSelector((state) => state.auth);

  // Fetch cart data when drawer opens
  useEffect(() => {
    if (cartDrawerOpen) {
      dispatch(fetchCart());
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [cartDrawerOpen, dispatch]);

  // Close drawer on clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (drawerRef.current && !drawerRef.current.contains(event.target) && !event.target.closest('.shopping-bag-trigger')) {
        dispatch(setCartDrawerOpen(false));
      }
    };
    if (cartDrawerOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [cartDrawerOpen, dispatch]);

  const handleClose = () => {
    dispatch(setCartDrawerOpen(false));
  };

  const handleQuantityChange = (item, newQuantity) => {
    if (newQuantity <= 0) {
      handleRemoveItem(item.id);
      return;
    }
    dispatch(updateCartItem({ itemId: item.id, quantity: newQuantity }))
      .unwrap()
      .catch((err) => toast.error(err || 'Không thể cập nhật số lượng'));
  };

  const handleRemoveItem = (itemId) => {
    setRemovingIds(prev => new Set([...prev, itemId]));
    setTimeout(() => {
      dispatch(removeCartItem(itemId))
        .unwrap()
        .then(() => toast.success('Đã xóa sản phẩm khỏi giỏ hàng'))
        .catch((err) => toast.error(err || 'Không thể xóa sản phẩm'))
        .finally(() => {
          setRemovingIds(prev => {
            const next = new Set(prev);
            next.delete(itemId);
            return next;
          });
        });
    }, 200);
  };

  const handleCheckout = () => {
    dispatch(setCartDrawerOpen(false));
    if (!isAuthenticated) {
      toast.error('Vui lòng đăng nhập để thực hiện thanh toán');
      navigate('/login', { state: { from: '/checkout' } });
      return;
    }
    const selectedItemIds = items.map(item => item.id);
    navigate('/checkout', { state: { selectedItemIds } });
  };

  return (
    <>
      {/* Backdrop overlay */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: cartDrawerOpen ? 1 : 0 }}
        transition={{ duration: 0.3 }}
        className={`fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[60] ${
          cartDrawerOpen ? 'pointer-events-auto' : 'pointer-events-none'
        }`}
        onClick={handleClose}
      />

      {/* Cart Drawer Container */}
      <motion.div
        ref={drawerRef}
        initial={{ x: '100%' }}
        animate={{ x: cartDrawerOpen ? 0 : '100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="fixed inset-y-0 right-0 z-[70] w-full sm:w-[400px] bg-white shadow-2xl flex flex-col"
      >
        {/* Header */}
        <div className="h-[60px] px-6 border-b border-slate-100 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <ShoppingBag className="w-5 h-5 text-slate-900" />
            <h2 className="text-lg font-semibold text-slate-900 font-display">Giỏ hàng của bạn</h2>
          </div>
          <motion.button
            onClick={handleClose}
            className="p-1 text-slate-400 hover:text-slate-900 rounded-md transition-colors"
            whileHover={{ scale: 1.1, rotate: 90 }}
            whileTap={{ scale: 0.9 }}
          >
            <X className="w-6 h-6" />
          </motion.button>
        </div>

        {/* Body (Scrollable items) */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading && items.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <motion.div
                className="w-8 h-8 border-4 border-slate-900 border-t-transparent rounded-full"
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
              />
            </div>
          ) : items.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="h-full flex flex-col items-center justify-center text-center space-y-4"
            >
              <div className="p-4 bg-slate-50 rounded-full text-slate-400">
                <ShoppingBag className="w-12 h-12" />
              </div>
              <div>
                <p className="text-slate-900 font-medium text-base">Giỏ hàng đang trống</p>
                <p className="text-slate-400 text-sm mt-1">Hãy tiếp tục mua sắm để chọn sản phẩm yêu thích.</p>
              </div>
              <button
                onClick={() => {
                  handleClose();
                  navigate('/products');
                }}
                className="px-4 py-2 border border-slate-900 text-slate-900 hover:bg-slate-50 rounded-md font-medium transition-colors text-sm"
              >
                Khám phá sản phẩm
              </button>
            </motion.div>
          ) : (
            <AnimatePresence>
              {items.map((item) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, x: 30 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 30, height: 0, marginBottom: 0, paddingBottom: 0 }}
                  transition={{ duration: 0.25 }}
                  className="flex gap-4 pb-4 border-b border-slate-100 last:border-b-0 last:pb-0 overflow-hidden"
                >
                  {/* Product Image */}
                  <div className="w-20 h-20 bg-slate-50 rounded-md overflow-hidden shrink-0 border border-slate-100 flex items-center justify-center">
                    {item.image ? (
                      <img
                        src={item.image}
                        alt={item.name}
                        className="w-full h-full object-contain p-1"
                      />
                    ) : (
                      <ShoppingBag className="w-8 h-8 text-slate-300" />
                    )}
                  </div>

                  {/* Item Details */}
                  <div className="flex-1 min-w-0 flex flex-col justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-slate-800 truncate" title={item.name}>
                        {item.name}
                      </h3>
                      {item.variant_name && (
                        <p className="text-xs text-slate-400 mt-0.5">Phân loại: {item.variant_name}</p>
                      )}
                    </div>

                    <div className="flex items-center justify-between mt-2">
                      {/* Quantity Selector */}
                      <div className="flex items-center border border-slate-200 rounded-md bg-white">
                        <motion.button
                          onClick={() => handleQuantityChange(item, item.quantity - 1)}
                          className="w-8 h-8 flex items-center justify-center text-slate-500 hover:text-slate-800 transition-colors"
                          whileTap={{ scale: 0.85 }}
                        >
                          <Minus className="w-3.5 h-3.5" />
                        </motion.button>
                        <motion.span
                          key={item.quantity}
                          initial={{ scale: 1.3 }}
                          animate={{ scale: 1 }}
                          className="w-8 text-center text-sm font-medium text-slate-800 select-none"
                        >
                          {item.quantity}
                        </motion.span>
                        <motion.button
                          onClick={() => handleQuantityChange(item, item.quantity + 1)}
                          className="w-8 h-8 flex items-center justify-center text-slate-500 hover:text-slate-800 transition-colors"
                          whileTap={{ scale: 0.85 }}
                        >
                          <Plus className="w-3.5 h-3.5" />
                        </motion.button>
                      </div>

                      {/* Price and delete button */}
                      <div className="flex items-center gap-3">
                        <motion.span
                          key={item.price * item.quantity}
                          initial={{ scale: 1.1, color: '#2563eb' }}
                          animate={{ scale: 1, color: '#0f172a' }}
                          className="text-sm font-semibold text-slate-900"
                        >
                          {item.price.toLocaleString('vi-VN')} đ
                        </motion.span>
                        <motion.button
                          onClick={() => handleRemoveItem(item.id)}
                          className="p-1 text-slate-400 hover:text-red-500 rounded transition-colors"
                          title="Xóa sản phẩm"
                          whileHover={{ scale: 1.15 }}
                          whileTap={{ scale: 0.9 }}
                        >
                          <Trash2 className="w-4 h-4" />
                        </motion.button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </div>

        {/* Footer */}
        <AnimatePresence>
          {items.length > 0 && (
            <motion.div
              initial={{ y: 50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 50, opacity: 0 }}
              className="sticky bottom-0 border-t border-slate-100 bg-white p-6 shadow-[0_-10px_40px_-10px_rgba(0,0,0,0.04)]"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-slate-500 text-sm font-medium">Tổng số tiền:</span>
                <motion.span
                  key={totalAmount}
                  initial={{ scale: 1.05, y: -4 }}
                  animate={{ scale: 1, y: 0 }}
                  className="text-2xl font-bold text-slate-900 font-display"
                >
                  {totalAmount.toLocaleString('vi-VN')} đ
                </motion.span>
              </div>
              <motion.button
                onClick={handleCheckout}
                className="w-full bg-slate-900 text-white py-4 rounded-md font-medium text-base hover:bg-slate-800 transition-colors flex items-center justify-center gap-2"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                Đặt đơn & Thanh toán
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </>
  );
};

export default CartDrawer;
