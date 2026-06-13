import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import { fetchCart, clearCart } from '../store/slices/cartSlice';
import CartItem from '../components/cart/CartItem';
import Empty from '../components/common/Empty';
import ProductRecommendations from '../components/product/ProductRecommendations';
import { ShoppingBagIcon, TrashIcon } from '@heroicons/react/24/outline';
import { formatPrice } from '../utils/format';
import toast from 'react-hot-toast';
import { staggerContainer, staggerItem } from '../utils/animations';

const CartPage = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { items } = useSelector((state) => state.cart);
  const { isAuthenticated } = useSelector((state) => state.auth);

  const [selectedItemIds, setSelectedItemIds] = useState([]);
  const [prevItemsCount, setPrevItemsCount] = useState(0);
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      dispatch(fetchCart());
    }
  }, [dispatch, isAuthenticated]);

  // Handle auto-selection of initial items and newly added items
  useEffect(() => {
    if (items && items.length > 0) {
      const itemIds = items.map(i => i.id);
      if (selectedItemIds.length === 0 && prevItemsCount === 0) {
        setSelectedItemIds(itemIds);
        setPrevItemsCount(items.length);
      } else if (items.length !== prevItemsCount) {
        setSelectedItemIds(prev => {
          const validPrev = prev.filter(id => itemIds.includes(id));
          const newItems = itemIds.filter(id => !prev.includes(id));
          return [...validPrev, ...newItems];
        });
        setPrevItemsCount(items.length);
      }
    } else {
      setSelectedItemIds([]);
      setPrevItemsCount(0);
    }
  }, [items, selectedItemIds.length, prevItemsCount]);

  const toggleSelectItem = (itemId) => {
    setSelectedItemIds(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const toggleSelectAll = () => {
    if (selectedItemIds.length === items.length) {
      setSelectedItemIds([]);
    } else {
      setSelectedItemIds(items.map(item => item.id));
    }
  };

  const handleClearCart = () => {
    if (window.confirm('Bạn có chắc muốn xóa toàn bộ giỏ hàng?')) {
      setClearing(true);
      dispatch(clearCart())
        .unwrap()
        .then(() => {
          toast.success('Đã xóa giỏ hàng');
          setClearing(false);
        })
        .catch((err) => {
          toast.error(err);
          setClearing(false);
        });
    }
  };

  const handleCheckout = () => {
    if (selectedItemIds.length === 0) {
      toast.error('Vui lòng chọn ít nhất một sản phẩm để thanh toán');
      return;
    }
    if (!isAuthenticated) {
      toast.error('Vui lòng đăng nhập để thanh toán');
      navigate('/login', { state: { from: '/checkout' } });
      return;
    }
    navigate('/checkout', { state: { selectedItemIds } });
  };

  const selectedItems = items.filter(item => selectedItemIds.includes(item.id));
  const selectedTotalAmount = selectedItems.reduce((sum, item) => sum + item.subtotal, 0);
  const selectedTotalItems = selectedItems.reduce((sum, item) => sum + item.quantity, 0);

  if (!items || items.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <Empty
          icon={<ShoppingBagIcon className="w-24 h-24" />}
          title="Giỏ hàng trống"
          description="Bạn chưa có sản phẩm nào trong giỏ hàng. Hãy khám phá và thêm sản phẩm yêu thích!"
          action={
            <Link to="/products" className="btn-primary">
              Tiếp tục mua sắm
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <motion.div
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
    >
      <motion.div variants={staggerItem} className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Giỏ hàng ({items.length} mặt hàng)
        </h1>
        <motion.button
          onClick={handleClearCart}
          className="text-red-500 hover:text-red-600 flex items-center"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
        >
          <TrashIcon className="w-5 h-5 mr-1" />
          Xóa tất cả
        </motion.button>
      </motion.div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Cart Items */}
        <div className="lg:col-span-2 space-y-4">
          {/* Header Card */}
          <motion.div variants={staggerItem} className="hidden md:flex items-center text-xs text-gray-500 bg-white px-6 py-4 rounded-lg shadow-sm border border-gray-100 font-medium">
            <div className="flex items-center space-x-3 flex-grow basis-[40%] min-w-0">
              <input
                type="checkbox"
                checked={items.length > 0 && selectedItemIds.length === items.length}
                onChange={toggleSelectAll}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 h-4 w-4 cursor-pointer accent-primary-600"
              />
              <span className="text-gray-700 font-semibold text-sm">Sản Phẩm</span>
            </div>
            <div className="w-[18%] text-center font-semibold text-sm">Phân Loại Hàng</div>
            <div className="w-[12%] text-center font-semibold text-sm">Đơn Giá</div>
            <div className="w-[12%] text-center font-semibold text-sm">Số Lượng</div>
            <div className="w-[12%] text-center font-semibold text-sm">Số Tiền</div>
            <div className="w-[8%] text-center font-semibold text-sm">Thao Tác</div>
          </motion.div>

          {/* Items List Card */}
          <motion.div variants={staggerItem} className="flex flex-col rounded-lg shadow-sm border border-gray-100 overflow-hidden bg-white divide-y divide-gray-100">
            <AnimatePresence mode="popLayout">
              {items.map((item) => (
                <motion.div
                  key={item.id}
                  layout
                  exit={{ opacity: 0, x: 50, height: 0, overflow: 'hidden' }}
                  transition={{ duration: 0.25 }}
                >
                  <CartItem
                    item={item}
                    isSelected={selectedItemIds.includes(item.id)}
                    onToggleSelect={() => toggleSelectItem(item.id)}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </motion.div>
        </div>

        {/* Order Summary */}
        <motion.div variants={staggerItem} className="lg:col-span-1">
          <div className="card p-6 sticky top-24">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Tổng đơn hàng</h2>

            <div className="space-y-3 border-b border-gray-200 pb-4 mb-4">
              <div className="flex justify-between text-gray-600">
                <span>Tạm tính ({selectedTotalItems} sản phẩm)</span>
                <span>{formatPrice(selectedTotalAmount)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Phí vận chuyển</span>
                <span className="text-green-600">Miễn phí</span>
              </div>
            </div>

            <div className="flex justify-between text-lg font-semibold text-gray-900 mb-6">
              <span>Tổng cộng</span>
              <motion.span
                key={selectedTotalAmount}
                initial={{ scale: 1.05 }}
                animate={{ scale: 1 }}
                className="text-red-600"
              >
                {formatPrice(selectedTotalAmount)}
              </motion.span>
            </div>

            <motion.button
              onClick={handleCheckout}
              className="btn-primary w-full mb-3"
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              Tiến hành thanh toán
            </motion.button>
            <Link to="/products" className="btn-secondary w-full text-center block">
              Tiếp tục mua sắm
            </Link>
          </div>
        </motion.div>
      </div>

      {/* AI Recommendations */}
      <div className="mt-12 border-t border-gray-200">
        {items && items.length > 0 && (
          <ProductRecommendations
            productId={items[0]?.product?.id || items[0]?.product_id}
            type="similar"
            title="Có thể bạn cũng thích"
            limit={6}
          />
        )}
        <ProductRecommendations
          type="trending"
          title="Sản phẩm bán chạy"
          limit={6}
        />
      </div>
    </motion.div>
  );
};

export default CartPage;
