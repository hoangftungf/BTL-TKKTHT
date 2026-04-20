import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { createOrder } from '../store/slices/orderSlice';
import { resetCart } from '../store/slices/cartSlice';
import { formatPrice } from '../utils/format';
import userService from '../services/userService';
import toast from 'react-hot-toast';
import { PlusIcon, MapPinIcon, CheckIcon } from '@heroicons/react/24/outline';

const CheckoutPage = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { items, totalAmount } = useSelector((state) => state.cart);
  const { loading } = useSelector((state) => state.order);

  const [addresses, setAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [loadingAddresses, setLoadingAddresses] = useState(true);

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

  const [newAddress, setNewAddress] = useState({
    recipient_name: '',
    phone: '',
    province: '',
    district: '',
    ward: '',
    street_address: '',
    address_type: 'home',
    is_default: false,
  });

  // Load addresses on mount
  useEffect(() => {
    loadAddresses();
  }, []);

  useEffect(() => {
    if (!items || items.length === 0) {
      navigate('/cart');
    }
  }, [items, navigate]);

  const loadAddresses = async () => {
    try {
      setLoadingAddresses(true);
      const data = await userService.getAddresses();
      setAddresses(data);

      // Auto-select default address
      const defaultAddr = data.find(addr => addr.is_default);
      if (defaultAddr) {
        selectAddress(defaultAddr);
      } else if (data.length > 0) {
        selectAddress(data[0]);
      }
    } catch (error) {
      console.error('Error loading addresses:', error);
    } finally {
      setLoadingAddresses(false);
    }
  };

  const selectAddress = (address) => {
    setSelectedAddressId(address.id);
    setFormData(prev => ({
      ...prev,
      recipient_name: address.recipient_name,
      recipient_phone: address.phone,
      shipping_address: address.street_address,
      shipping_province: address.province,
      shipping_district: address.district,
      shipping_ward: address.ward,
    }));
    setShowAddForm(false);
  };

  const handleAddAddress = async (e) => {
    e.preventDefault();

    if (!newAddress.recipient_name || !newAddress.phone || !newAddress.street_address) {
      toast.error('Vui lòng điền đầy đủ thông tin');
      return;
    }

    try {
      const created = await userService.addAddress(newAddress);
      toast.success('Thêm địa chỉ thành công');
      setAddresses([...addresses, created]);
      selectAddress(created);
      setShowAddForm(false);
      setNewAddress({
        recipient_name: '',
        phone: '',
        province: '',
        district: '',
        ward: '',
        street_address: '',
        address_type: 'home',
        is_default: false,
      });
    } catch (error) {
      toast.error('Không thể thêm địa chỉ');
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleNewAddressChange = (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setNewAddress({ ...newAddress, [e.target.name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.recipient_name || !formData.recipient_phone || !formData.shipping_address) {
      toast.error('Vui lòng chọn hoặc thêm địa chỉ giao hàng');
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
            {/* Address Selection */}
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                  <MapPinIcon className="w-5 h-5 mr-2 text-primary-600" />
                  Địa chỉ giao hàng
                </h2>
                <button
                  type="button"
                  onClick={() => setShowAddForm(!showAddForm)}
                  className="flex items-center text-primary-600 hover:text-primary-700 text-sm font-medium"
                >
                  <PlusIcon className="w-4 h-4 mr-1" />
                  Thêm địa chỉ mới
                </button>
              </div>

              {loadingAddresses ? (
                <div className="text-center py-8 text-gray-500">Đang tải địa chỉ...</div>
              ) : (
                <>
                  {/* Saved Addresses */}
                  {addresses.length > 0 && (
                    <div className="space-y-3 mb-4">
                      {addresses.map((address) => (
                        <div
                          key={address.id}
                          onClick={() => selectAddress(address)}
                          className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                            selectedAddressId === address.id
                              ? 'border-primary-500 bg-primary-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-grow">
                              <div className="flex items-center mb-1">
                                <span className="font-medium text-gray-900">{address.recipient_name}</span>
                                <span className="mx-2 text-gray-300">|</span>
                                <span className="text-gray-600">{address.phone}</span>
                                {address.is_default && (
                                  <span className="ml-2 px-2 py-0.5 bg-primary-100 text-primary-700 text-xs rounded">
                                    Mặc định
                                  </span>
                                )}
                                <span className="ml-2 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded capitalize">
                                  {address.address_type === 'home' ? 'Nhà riêng' : address.address_type === 'office' ? 'Văn phòng' : 'Khác'}
                                </span>
                              </div>
                              <p className="text-gray-600 text-sm">
                                {address.street_address}, {address.ward}, {address.district}, {address.province}
                              </p>
                            </div>
                            {selectedAddressId === address.id && (
                              <CheckIcon className="w-6 h-6 text-primary-600 flex-shrink-0" />
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* No addresses message */}
                  {addresses.length === 0 && !showAddForm && (
                    <div className="text-center py-8 bg-gray-50 rounded-lg">
                      <MapPinIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                      <p className="text-gray-500 mb-3">Bạn chưa có địa chỉ nào</p>
                      <button
                        type="button"
                        onClick={() => setShowAddForm(true)}
                        className="btn-primary"
                      >
                        Thêm địa chỉ đầu tiên
                      </button>
                    </div>
                  )}

                  {/* Add New Address Form */}
                  {showAddForm && (
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 bg-gray-50">
                      <h3 className="font-medium text-gray-900 mb-4">Thêm địa chỉ mới</h3>
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Họ và tên *</label>
                          <input
                            type="text"
                            name="recipient_name"
                            value={newAddress.recipient_name}
                            onChange={handleNewAddressChange}
                            className="input"
                            placeholder="Nguyễn Văn A"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Số điện thoại *</label>
                          <input
                            type="tel"
                            name="phone"
                            value={newAddress.phone}
                            onChange={handleNewAddressChange}
                            className="input"
                            placeholder="0912345678"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Tỉnh/Thành phố *</label>
                          <input
                            type="text"
                            name="province"
                            value={newAddress.province}
                            onChange={handleNewAddressChange}
                            className="input"
                            placeholder="Hà Nội"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Quận/Huyện *</label>
                          <input
                            type="text"
                            name="district"
                            value={newAddress.district}
                            onChange={handleNewAddressChange}
                            className="input"
                            placeholder="Cầu Giấy"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Phường/Xã *</label>
                          <input
                            type="text"
                            name="ward"
                            value={newAddress.ward}
                            onChange={handleNewAddressChange}
                            className="input"
                            placeholder="Dịch Vọng"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Loại địa chỉ</label>
                          <select
                            name="address_type"
                            value={newAddress.address_type}
                            onChange={handleNewAddressChange}
                            className="input"
                          >
                            <option value="home">Nhà riêng</option>
                            <option value="office">Văn phòng</option>
                            <option value="other">Khác</option>
                          </select>
                        </div>
                        <div className="md:col-span-2">
                          <label className="block text-sm font-medium text-gray-700 mb-1">Địa chỉ chi tiết *</label>
                          <input
                            type="text"
                            name="street_address"
                            value={newAddress.street_address}
                            onChange={handleNewAddressChange}
                            className="input"
                            placeholder="Số nhà, tên đường..."
                          />
                        </div>
                        <div className="md:col-span-2">
                          <label className="flex items-center">
                            <input
                              type="checkbox"
                              name="is_default"
                              checked={newAddress.is_default}
                              onChange={handleNewAddressChange}
                              className="mr-2"
                            />
                            <span className="text-sm text-gray-700">Đặt làm địa chỉ mặc định</span>
                          </label>
                        </div>
                      </div>
                      <div className="flex justify-end space-x-3 mt-4">
                        <button
                          type="button"
                          onClick={() => setShowAddForm(false)}
                          className="btn-secondary"
                        >
                          Hủy
                        </button>
                        <button
                          type="button"
                          onClick={handleAddAddress}
                          className="btn-primary"
                        >
                          Lưu địa chỉ
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Note */}
            <div className="card p-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">Ghi chú cho đơn hàng</label>
              <textarea
                name="note"
                value={formData.note}
                onChange={handleChange}
                className="input"
                rows="2"
                placeholder="Ví dụ: Giao hàng giờ hành chính..."
              />
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

              <button
                type="submit"
                disabled={loading || !selectedAddressId}
                className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Đang xử lý...' : 'Đặt hàng'}
              </button>

              {!selectedAddressId && (
                <p className="text-sm text-red-500 text-center mt-2">
                  Vui lòng chọn địa chỉ giao hàng
                </p>
              )}
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default CheckoutPage;
