import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchOrders } from '../store/slices/orderSlice';
import Loading from '../components/common/Loading';
import Empty from '../components/common/Empty';
import { ClipboardDocumentListIcon } from '@heroicons/react/24/outline';
import { formatPrice, formatDateTime, formatOrderStatus, getStatusColor } from '../utils/format';

const OrdersPage = () => {
  const dispatch = useDispatch();
  const { orders, loading } = useSelector((state) => state.order);

  useEffect(() => {
    dispatch(fetchOrders());
  }, [dispatch]);

  if (loading) {
    return <Loading />;
  }

  if (!orders || orders.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <Empty
          icon={<ClipboardDocumentListIcon className="w-24 h-24" />}
          title="Chưa có đơn hàng"
          description="Bạn chưa có đơn hàng nào. Hãy khám phá và mua sắm ngay!"
          action={
            <Link to="/products" className="btn-primary">
              Mua sắm ngay
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">Đơn hàng của tôi</h1>

      <div className="space-y-4">
        {orders.map((order) => (
          <Link
            key={order.id}
            to={`/orders/${order.id}`}
            className="card p-6 block hover:shadow-md transition-shadow"
          >
            <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
              <div>
                <p className="font-medium text-gray-900">Đơn hàng #{order.order_number}</p>
                <p className="text-sm text-gray-500">{formatDateTime(order.created_at)}</p>
              </div>
              <div className="text-right">
                <span className={getStatusColor(order.status)}>
                  {formatOrderStatus(order.status)}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
              <p className="text-gray-600">{order.item_count} sản phẩm</p>
              <p className="font-semibold text-lg">{formatPrice(order.total_amount)}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default OrdersPage;
