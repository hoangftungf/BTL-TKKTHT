import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchCart, clearCart } from '../store/slices/cartSlice';
import CartItem from '../components/cart/CartItem';
import Loading from '../components/common/Loading';
import Empty from '../components/common/Empty';
import { ShoppingBagIcon, TrashIcon } from '@heroicons/react/24/outline';
import { formatPrice } from '../utils/format';
import toast from 'react-hot-toast';

const CartPage = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { items, totalItems, totalAmount, loading } = useSelector((state) => state.cart);
  const { isAuthenticated } = useSelector((state) => state.auth);

  useEffect(() => {
    if (isAuthenticated) {
      dispatch(fetchCart());
    }
  }, [dispatch, isAuthenticated]);

  const handleClearCart = () => {
    if (window.confirm('Bạn có chắc muốn xóa toàn bộ giỏ hàng?')) {
      dispatch(clearCart())
        .unwrap()
        .then(() => toast.success('Đã xóa giỏ hàng'))
        .catch((err) => toast.error(err));
    }
  };

  const handleCheckout = () => {
    if (!isAuthenticated) {
      toast.error('Vui lòng đăng nhập để thanh toán');
      navigate('/login', { state: { from: '/checkout' } });
      return;
    }
    navigate('/checkout');
  };

  if (loading) {
    return <Loading />;
  }

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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Giỏ hàng ({totalItems} sản phẩm)
        </h1>
        <button onClick={handleClearCart} className="text-red-500 hover:text-red-600 flex items-center">
          <TrashIcon className="w-5 h-5 mr-1" />
          Xóa tất cả
        </button>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Cart Items */}
        <div className="lg:col-span-2">
          <div className="card p-6">
            {items.map((item) => (
              <CartItem key={item.id} item={item} />
            ))}
          </div>
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <div className="card p-6 sticky top-24">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Tổng đơn hàng</h2>

            <div className="space-y-3 border-b border-gray-200 pb-4 mb-4">
              <div className="flex justify-between text-gray-600">
                <span>Tạm tính</span>
                <span>{formatPrice(totalAmount)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Phí vận chuyển</span>
                <span className="text-green-600">Miễn phí</span>
              </div>
            </div>

            <div className="flex justify-between text-lg font-semibold text-gray-900 mb-6">
              <span>Tổng cộng</span>
              <span className="text-red-600">{formatPrice(totalAmount)}</span>
            </div>

            <button onClick={handleCheckout} className="btn-primary w-full mb-3">
              Tiến hành thanh toán
            </button>
            <Link to="/products" className="btn-secondary w-full text-center block">
              Tiếp tục mua sắm
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CartPage;
