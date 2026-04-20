import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { createOrder } from '../store/slices/orderSlice';
import { resetCart } from '../store/slices/cartSlice';
import { formatPrice } from '../utils/format';
import toast from 'react-hot-toast';

const CheckoutPage = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { items, totalAmount } = useSelector((state) => state.cart);
  const { loading } = useSelector((state) => state.order);

  const [formData, setFormData] = useState({
    recipient_name: '',
    recipient_phone: '',
    shipping_address: '',
    shipping_province: '',
    shipping_district: '',
    shipping_ward: '',
    payment_method: 'cod',
    note: '',
  });

  useEffect(() => {
    if (!items || items.length === 0) {
      navigate('/cart');
    }
  }, [items, navigate]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.recipient_name || !formData.recipient_phone || !formData.shipping_address) {
      toast.error('Vui lòng điền đầy đủ thông tin');
      return;
    }

    dispatch(createOrder(formData))
      .unwrap()
      .then((order) => {
        dispatch(resetCart());
        toast.success('Đặt hàng thành công!');
        navigate(`/orders/${order.id}`);
      })
      .catch((err) => toast.error(err));
  };

  const shippingFee = 30000;
  const total = totalAmount + shippingFee;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">Thanh toán</h1>

      <form onSubmit={handleSubmit}>
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Shipping Info */}
          <div className="lg:col-span-2 space-y-6">
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Thông tin giao hàng</h2>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Họ và tên *</label>
                  <input
                    type="text"
                    name="recipient_name"
                    value={formData.recipient_name}
                    onChange={handleChange}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Số điện thoại *</label>
                  <input
                    type="tel"
                    name="recipient_phone"
                    value={formData.recipient_phone}
                    onChange={handleChange}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tỉnh/Thành phố *</label>
                  <input
                    type="text"
                    name="shipping_province"
                    value={formData.shipping_province}
                    onChange={handleChange}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Quận/Huyện *</label>
                  <input
                    type="text"
                    name="shipping_district"
                    value={formData.shipping_district}
                    onChange={handleChange}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phường/Xã *</label>
                  <input
                    type="text"
                    name="shipping_ward"
                    value={formData.shipping_ward}
                    onChange={handleChange}
                    className="input"
                    required
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Địa chỉ chi tiết *</label>
                  <input
                    type="text"
                    name="shipping_address"
                    value={formData.shipping_address}
                    onChange={handleChange}
                    className="input"
                    placeholder="Số nhà, tên đường..."
                    required
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ghi chú</label>
                  <textarea
                    name="note"
                    value={formData.note}
                    onChange={handleChange}
                    className="input"
                    rows="3"
                    placeholder="Ghi chú cho đơn hàng..."
                  />
                </div>
              </div>
            </div>

            {/* Payment Method */}
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Phương thức thanh toán</h2>

              <div className="space-y-3">
                {[
                  { value: 'cod', label: 'Thanh toán khi nhận hàng (COD)', icon: '💵' },
                  { value: 'momo', label: 'Ví MoMo', icon: '📱' },
                  { value: 'vnpay', label: 'VNPay', icon: '💳' },
                ].map((method) => (
                  <label
                    key={method.value}
                    className={`flex items-center p-4 border rounded-lg cursor-pointer transition-all ${
                      formData.payment_method === method.value
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="payment_method"
                      value={method.value}
                      checked={formData.payment_method === method.value}
                      onChange={handleChange}
                      className="mr-3"
                    />
                    <span className="mr-3 text-2xl">{method.icon}</span>
                    <span className="font-medium">{method.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="card p-6 sticky top-24">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Đơn hàng của bạn</h2>

              <div className="space-y-3 border-b border-gray-200 pb-4 mb-4 max-h-64 overflow-y-auto">
                {items.map((item) => (
                  <div key={item.id} className="flex items-center space-x-3">
                    <div className="w-16 h-16 rounded-lg bg-gray-100 overflow-hidden flex-shrink-0">
                      <img src={item.product_image || '/placeholder.png'} alt="" className="w-full h-full object-cover" />
                    </div>
                    <div className="flex-grow min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{item.product_name}</p>
                      <p className="text-sm text-gray-500">x{item.quantity}</p>
                    </div>
                    <span className="text-sm font-medium">{formatPrice(item.subtotal)}</span>
                  </div>
                ))}
              </div>

              <div className="space-y-2 border-b border-gray-200 pb-4 mb-4">
                <div className="flex justify-between text-gray-600">
                  <span>Tạm tính</span>
                  <span>{formatPrice(totalAmount)}</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Phí vận chuyển</span>
                  <span>{formatPrice(shippingFee)}</span>
                </div>
              </div>

              <div className="flex justify-between text-lg font-semibold text-gray-900 mb-6">
                <span>Tổng cộng</span>
                <span className="text-red-600">{formatPrice(total)}</span>
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full">
                {loading ? 'Đang xử lý...' : 'Đặt hàng'}
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default CheckoutPage;
