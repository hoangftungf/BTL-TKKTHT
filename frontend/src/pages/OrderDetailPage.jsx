import { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchOrderById, cancelOrder } from '../store/slices/orderSlice';
import Loading from '../components/common/Loading';
import { formatPrice, formatDateTime, formatOrderStatus, formatPaymentStatus, getStatusColor } from '../utils/format';
import toast from 'react-hot-toast';

const OrderDetailPage = () => {
  const { id } = useParams();
  const dispatch = useDispatch();
  const { currentOrder: order, loading } = useSelector((state) => state.order);

  useEffect(() => {
    dispatch(fetchOrderById(id));
  }, [dispatch, id]);

  const handleCancel = () => {
    if (window.confirm('Bạn có chắc muốn hủy đơn hàng này?')) {
      dispatch(cancelOrder({ orderId: id, reason: 'Khách hàng hủy đơn' }))
        .unwrap()
        .then(() => toast.success('Đã hủy đơn hàng'))
        .catch((err) => toast.error(err));
    }
  };

  if (loading || !order) {
    return <Loading />;
  }

  const canCancel = ['pending', 'confirmed'].includes(order.status);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <Link to="/orders" className="text-primary-600 hover:underline text-sm mb-2 inline-block">
            ← Quay lại đơn hàng
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Đơn hàng #{order.order_number}</h1>
        </div>
        {canCancel && (
          <button onClick={handleCancel} className="btn-danger">
            Hủy đơn hàng
          </button>
        )}
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* Status */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <span className={`text-lg ${getStatusColor(order.status)}`}>
                  {formatOrderStatus(order.status)}
                </span>
                <p className="text-gray-500 text-sm mt-1">
                  Đặt hàng lúc: {formatDateTime(order.created_at)}
                </p>
              </div>
              <div className="text-right">
                <span className={getStatusColor(order.payment_status)}>
                  {formatPaymentStatus(order.payment_status)}
                </span>
              </div>
            </div>
          </div>

          {/* Items */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Sản phẩm</h2>
            <div className="space-y-4">
              {order.items?.map((item) => (
                <div key={item.id} className="flex items-center space-x-4">
                  <div className="w-20 h-20 rounded-lg bg-gray-100 overflow-hidden">
                    <img src={item.product_image || '/placeholder.png'} alt="" className="w-full h-full object-cover" />
                  </div>
                  <div className="flex-grow">
                    <p className="font-medium text-gray-900">{item.product_name}</p>
                    <p className="text-gray-500 text-sm">SKU: {item.sku}</p>
                    <p className="text-gray-500 text-sm">Số lượng: {item.quantity}</p>
                  </div>
                  <p className="font-semibold">{formatPrice(item.subtotal)}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Shipping Info */}
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Thông tin giao hàng</h2>
            <div className="text-gray-600">
              <p className="font-medium text-gray-900">{order.recipient_name}</p>
              <p>{order.recipient_phone}</p>
              <p className="mt-2">
                {order.shipping_address}, {order.shipping_ward}, {order.shipping_district}, {order.shipping_province}
              </p>
              {order.note && (
                <p className="mt-2 text-sm italic">Ghi chú: {order.note}</p>
              )}
            </div>
          </div>
        </div>

        {/* Summary */}
        <div className="lg:col-span-1">
          <div className="card p-6 sticky top-24">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Tổng đơn hàng</h2>

            <div className="space-y-3 border-b border-gray-200 pb-4 mb-4">
              <div className="flex justify-between text-gray-600">
                <span>Tạm tính</span>
                <span>{formatPrice(order.subtotal)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Phí vận chuyển</span>
                <span>{formatPrice(order.shipping_fee)}</span>
              </div>
              {order.discount_amount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Giảm giá</span>
                  <span>-{formatPrice(order.discount_amount)}</span>
                </div>
              )}
            </div>

            <div className="flex justify-between text-lg font-semibold text-gray-900">
              <span>Tổng cộng</span>
              <span className="text-red-600">{formatPrice(order.total_amount)}</span>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-gray-500 text-sm">
                Phương thức thanh toán: <span className="text-gray-900">{order.payment_method_display}</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderDetailPage;
