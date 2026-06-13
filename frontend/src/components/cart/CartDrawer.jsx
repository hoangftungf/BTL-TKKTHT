import { useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { X, Plus, Minus, Trash2, ShoppingBag } from 'lucide-react';
import { fetchCart, updateCartItem, removeCartItem } from '../../store/slices/cartSlice';
import { setCartDrawerOpen } from '../../store/slices/uiSlice';
import toast from 'react-hot-toast';

const CartDrawer = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const drawerRef = useRef(null);

  const { cartDrawerOpen } = useSelector((state) => state.ui);
  const { items, totalAmount, loading } = useSelector((state) => state.cart);
  const { isAuthenticated } = useSelector((state) => state.auth);

  // Fetch cart data when drawer opens
  useEffect(() => {
    if (cartDrawerOpen) {
      dispatch(fetchCart());
      // Prevent body scrolling when drawer is open
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
    dispatch(removeCartItem(itemId))
      .unwrap()
      .then(() => toast.success('Đã xóa sản phẩm khỏi giỏ hàng'))
      .catch((err) => toast.error(err || 'Không thể xóa sản phẩm'));
  };

  const handleCheckout = () => {
    dispatch(setCartDrawerOpen(false));
    if (!isAuthenticated) {
      toast.error('Vui lòng đăng nhập để thực hiện thanh toán');
      navigate('/login', { state: { from: '/checkout' } });
      return;
    }
    // Check out all items in the cart
    const selectedItemIds = items.map(item => item.id);
    navigate('/checkout', { state: { selectedItemIds } });
  };

  return (
    <>
      {/* Backdrop overlay */}
      <div
        className={`fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[60] transition-opacity duration-300 ${
          cartDrawerOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={handleClose}
      />

      {/* Cart Drawer Container */}
      <div
        ref={drawerRef}
        className={`fixed inset-y-0 right-0 z-[70] w-full sm:w-[400px] bg-white shadow-2xl flex flex-col transform transition-transform duration-300 ease-in-out ${
          cartDrawerOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="h-[60px] px-6 border-b border-slate-100 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <ShoppingBag className="w-5 h-5 text-slate-900" />
            <h2 className="text-lg font-semibold text-slate-900 font-display">Giỏ hàng của bạn</h2>
          </div>
          <button
            onClick={handleClose}
            className="p-1 text-slate-400 hover:text-slate-900 rounded-md transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Body (Scrollable items) */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading && items.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <svg className="animate-spin h-8 w-8 text-slate-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          ) : items.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-4">
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
            </div>
          ) : (
            items.map((item) => (
              <div key={item.id} className="flex gap-4 pb-4 border-b border-slate-100 last:border-b-0 last:pb-0">
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
                    {/* Quantity Selector with min 40px touch targets */}
                    <div className="flex items-center border border-slate-200 rounded-md bg-white">
                      <button
                        onClick={() => handleQuantityChange(item, item.quantity - 1)}
                        className="w-8 h-8 flex items-center justify-center text-slate-500 hover:text-slate-800 transition-colors"
                      >
                        <Minus className="w-3.5 h-3.5" />
                      </button>
                      <span className="w-8 text-center text-sm font-medium text-slate-800 select-none">
                        {item.quantity}
                      </span>
                      <button
                        onClick={() => handleQuantityChange(item, item.quantity + 1)}
                        className="w-8 h-8 flex items-center justify-center text-slate-500 hover:text-slate-800 transition-colors"
                      >
                        <Plus className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {/* Price and delete button */}
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-semibold text-slate-900">
                        {item.price.toLocaleString('vi-VN')} đ
                      </span>
                      <button
                        onClick={() => handleRemoveItem(item.id)}
                        className="p-1 text-slate-400 hover:text-red-500 rounded transition-colors"
                        title="Xóa sản phẩm"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        {items.length > 0 && (
          <div className="sticky bottom-0 border-t border-slate-100 bg-white p-6 shadow-[0_-10px_40px_-10px_rgba(0,0,0,0.04)]">
            <div className="flex items-center justify-between mb-4">
              <span className="text-slate-500 text-sm font-medium">Tổng số tiền:</span>
              <span className="text-2xl font-bold text-slate-900 font-display">
                {totalAmount.toLocaleString('vi-VN')} đ
              </span>
            </div>
            <button
              onClick={handleCheckout}
              className="w-full bg-slate-900 text-white py-4 rounded-md font-medium text-base hover:bg-slate-800 transition-colors flex items-center justify-center gap-2 active:bg-slate-950"
            >
              Đặt đơn & Thanh toán
            </button>
          </div>
        )}
      </div>
    </>
  );
};

export default CartDrawer;
