import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import orderService from '../../services/orderService';
import {
  ClipboardDocumentListIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon,
  XMarkIcon,
  CalendarDaysIcon,
  UserIcon,
  CreditCardIcon,
  MapPinIcon
} from '@heroicons/react/24/outline';

const AdminOrdersPage = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Detail Modal states
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [statusNote, setStatusNote] = useState('');

  useEffect(() => {
    fetchOrders();
  }, [statusFilter]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const params = {};
      if (statusFilter) params.status = statusFilter;
      const data = await orderService.getOrders(params);
      
      // Filter orders on client side if search query is provided
      let filteredOrders = data || [];
      if (searchQuery.trim()) {
        filteredOrders = filteredOrders.filter(o => 
          o.order_number.toLowerCase().includes(searchQuery.toLowerCase()) || 
          o.user_id.toLowerCase().includes(searchQuery.toLowerCase())
        );
      }
      setOrders(filteredOrders);
    } catch (error) {
      console.error('Fetch orders error:', error);
      toast.error('Không thể tải danh sách đơn hàng');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchOrders();
  };

  const openOrderDetail = async (order) => {
    const loadingToast = toast.loading('Đang tải chi tiết đơn hàng...');
    try {
      const detail = await orderService.getOrderById(order.id);
      setSelectedOrder(detail);
      setStatusNote('');
      setIsDetailModalOpen(true);
      toast.dismiss(loadingToast);
    } catch (error) {
      console.error('Fetch order detail error:', error);
      toast.error('Không thể lấy chi tiết đơn hàng', { id: loadingToast });
    }
  };

  const handleUpdateStatus = async (newStatus) => {
    if (!selectedOrder) return;
    
    setUpdatingStatus(true);
    const loadingToast = toast.loading(`Đang cập nhật trạng thái đơn hàng sang ${newStatus}...`);
    try {
      const response = await orderService.updateOrderStatus(selectedOrder.id, newStatus, statusNote);
      toast.success('Cập nhật trạng thái thành công!', { id: loadingToast });
      
      // Refresh details and order list
      setSelectedOrder(response.order);
      setStatusNote('');
      fetchOrders();
    } catch (error) {
      console.error('Update order status error:', error);
      toast.error(error.response?.data?.error || 'Không thể cập nhật trạng thái đơn hàng', { id: loadingToast });
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleCancelOrder = async () => {
    if (!selectedOrder) return;
    if (!window.confirm('Bạn có chắc chắn muốn hủy đơn hàng này không?')) return;

    setUpdatingStatus(true);
    const loadingToast = toast.loading('Đang hủy đơn hàng...');
    try {
      const response = await orderService.cancelOrder(selectedOrder.id, statusNote || 'Hủy bởi Admin');
      toast.success('Hủy đơn hàng thành công!', { id: loadingToast });
      setSelectedOrder(response.order);
      setStatusNote('');
      fetchOrders();
    } catch (error) {
      console.error('Cancel order error:', error);
      toast.error('Không thể hủy đơn hàng', { id: loadingToast });
    } finally {
      setUpdatingStatus(false);
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-amber-950/20 text-amber-400 border-amber-900/40';
      case 'confirmed':
        return 'bg-blue-950/20 text-blue-400 border-blue-900/40';
      case 'processing':
        return 'bg-indigo-950/20 text-indigo-400 border-indigo-900/40';
      case 'shipping':
        return 'bg-purple-950/20 text-purple-400 border-purple-900/40';
      case 'delivered':
        return 'bg-emerald-950/20 text-emerald-400 border-emerald-900/40';
      case 'cancelled':
        return 'bg-rose-950/20 text-rose-400 border-rose-900/40';
      default:
        return 'bg-slate-900 text-slate-400 border-slate-800';
    }
  };

  const getStatusDisplay = (status) => {
    switch (status) {
      case 'pending': return 'Chờ xác nhận';
      case 'confirmed': return 'Đã xác nhận';
      case 'processing': return 'Đang xử lý';
      case 'shipping': return 'Đang giao hàng';
      case 'delivered': return 'Đã giao hàng';
      case 'cancelled': return 'Đã hủy';
      default: return status;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800/80 shadow-xl">
        <h2 className="text-2xl font-bold text-white tracking-wide">Quản lý Đơn hàng</h2>
        <p className="text-slate-400 text-sm mt-0.5">Theo dõi lịch trình vận chuyển, doanh số đơn hàng và xử lý duyệt/hủy đơn của khách hàng.</p>
      </div>

      {/* Filters Bar */}
      <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/60 flex flex-col md:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:max-w-xs">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm theo Mã đơn..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <MagnifyingGlassIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-500" />
        </form>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center space-x-2 bg-slate-900 px-3 py-2 rounded-xl border border-slate-800 w-full md:w-auto">
            <FunnelIcon className="w-4 h-4 text-slate-500" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent text-xs text-slate-300 font-semibold focus:outline-none border-none pr-6 cursor-pointer"
            >
              <option value="" className="bg-slate-900">Tất cả trạng thái</option>
              <option value="pending" className="bg-slate-900">Chờ xác nhận</option>
              <option value="confirmed" className="bg-slate-900">Đã xác nhận</option>
              <option value="processing" className="bg-slate-900">Đang xử lý</option>
              <option value="shipping" className="bg-slate-900">Đang giao</option>
              <option value="delivered" className="bg-slate-900">Đã giao</option>
              <option value="cancelled" className="bg-slate-900">Đã hủy</option>
            </select>
          </div>

          <button 
            onClick={() => {
              setSearchQuery('');
              setStatusFilter('');
            }}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors focus:outline-none"
            title="Làm mới bộ lọc"
          >
            <ArrowPathIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Orders List Table */}
      <div className="bg-slate-950 rounded-2xl border border-slate-800/80 shadow-xl overflow-hidden">
        {loading ? (
          <div className="p-20 flex flex-col items-center justify-center space-y-4">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-indigo-500"></div>
            <p className="text-slate-400 text-sm">Đang tải danh sách đơn hàng...</p>
          </div>
        ) : orders.length === 0 ? (
          <div className="p-20 text-center space-y-2">
            <ClipboardDocumentListIcon className="w-12 h-12 text-slate-700 mx-auto" />
            <p className="text-slate-400 text-sm font-medium">Không tìm thấy đơn hàng nào</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-950 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="py-4 px-6">Mã đơn hàng</th>
                  <th className="py-4 px-6">Ngày đặt</th>
                  <th className="py-4 px-6">Mã khách hàng</th>
                  <th className="py-4 px-6">Tổng tiền</th>
                  <th className="py-4 px-6">Phương thức</th>
                  <th className="py-4 px-6">Trạng thái</th>
                  <th className="py-4 px-6 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850">
                {orders.map((order) => (
                  <tr key={order.id} className="hover:bg-slate-900/35 transition-colors">
                    <td className="py-4 px-6 font-mono text-sm text-indigo-400 font-bold">
                      #{order.order_number}
                    </td>
                    <td className="py-4 px-6 text-sm text-slate-300">
                      {new Date(order.created_at).toLocaleDateString('vi-VN', {
                        year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
                      })}
                    </td>
                    <td className="py-4 px-6 text-xs text-slate-500 font-mono font-semibold max-w-[120px] truncate">
                      {order.user_id}
                    </td>
                    <td className="py-4 px-6 text-sm font-bold text-white">
                      ${parseFloat(order.total_amount).toFixed(2)}
                    </td>
                    <td className="py-4 px-6 text-xs text-slate-400 uppercase font-semibold">
                      {order.payment_method || 'COD'}
                    </td>
                    <td className="py-4 px-6">
                      <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border uppercase tracking-wider ${getStatusBadgeClass(order.status)}`}>
                        {getStatusDisplay(order.status)}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <button 
                        onClick={() => openOrderDetail(order)}
                        className="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-semibold text-indigo-400 hover:text-indigo-300 hover:bg-slate-850 transition-colors focus:outline-none"
                      >
                        Chi tiết
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ============================================================
          ORDER DETAIL MODAL
          ============================================================ */}
      {isDetailModalOpen && selectedOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity duration-300"
            onClick={() => setIsDetailModalOpen(false)}
          />

          {/* Modal Container */}
          <div className="relative w-full max-w-3xl bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl z-10 overflow-hidden flex flex-col justify-between max-h-[90vh]">
            {/* Header */}
            <div className="h-16 flex items-center justify-between px-6 border-b border-slate-800/80 bg-slate-950">
              <div>
                <h3 className="text-base font-bold text-white">Chi tiết đơn hàng #{selectedOrder.order_number}</h3>
                <span className="text-[10px] text-slate-500 font-mono">{selectedOrder.id}</span>
              </div>
              <button 
                onClick={() => setIsDetailModalOpen(false)}
                className="p-1 rounded-md text-slate-400 hover:text-white focus:outline-none"
              >
                <XMarkIcon className="w-5.5 h-5.5" />
              </button>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Top row info */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-900 p-4 rounded-xl border border-slate-850 flex items-center space-x-3">
                  <CalendarDaysIcon className="w-7 h-7 text-indigo-400 flex-shrink-0" />
                  <div>
                    <span className="text-[10px] text-slate-500 font-semibold block uppercase">Ngày tạo</span>
                    <span className="text-xs text-white font-medium">
                      {new Date(selectedOrder.created_at).toLocaleString('vi-VN')}
                    </span>
                  </div>
                </div>

                <div className="bg-slate-900 p-4 rounded-xl border border-slate-850 flex items-center space-x-3">
                  <UserIcon className="w-7 h-7 text-indigo-400 flex-shrink-0" />
                  <div className="min-w-0">
                    <span className="text-[10px] text-slate-500 font-semibold block uppercase">ID Khách hàng</span>
                    <span className="text-xs text-white font-mono font-medium truncate block">
                      {selectedOrder.user_id}
                    </span>
                  </div>
                </div>

                <div className="bg-slate-900 p-4 rounded-xl border border-slate-850 flex items-center space-x-3">
                  <CreditCardIcon className="w-7 h-7 text-indigo-400 flex-shrink-0" />
                  <div>
                    <span className="text-[10px] text-slate-500 font-semibold block uppercase">Thanh toán</span>
                    <span className="text-xs text-white font-medium uppercase">
                      {selectedOrder.payment_method || 'COD'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Shipping info */}
              <div className="bg-slate-900 p-4 rounded-xl border border-slate-850 space-y-2">
                <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                  <MapPinIcon className="w-4.5 h-4.5 text-indigo-400" />
                  <h4 className="text-xs font-bold text-slate-300 uppercase">Thông tin giao nhận</h4>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div>
                    <p className="text-slate-500">Người nhận:</p>
                    <p className="text-slate-300 font-medium">{selectedOrder.shipping_name || 'N/A'}</p>
                    <p className="text-slate-500 mt-2">Số điện thoại:</p>
                    <p className="text-slate-300 font-medium">{selectedOrder.shipping_phone || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Địa chỉ giao hàng:</p>
                    <p className="text-slate-300 font-medium leading-relaxed">{selectedOrder.shipping_address || 'N/A'}</p>
                  </div>
                </div>
              </div>

              {/* Items List */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Danh sách sản phẩm mua ({selectedOrder.items?.length || 0})</h4>
                <div className="border border-slate-800 rounded-xl overflow-hidden divide-y divide-slate-850">
                  {selectedOrder.items?.map((item) => (
                    <div key={item.id} className="p-3.5 bg-slate-900/40 flex items-center justify-between text-sm">
                      <div className="min-w-0">
                        <p className="font-semibold text-white truncate">{item.product_name || 'Sản phẩm'}</p>
                        <p className="text-xs text-slate-500">ID Sản phẩm: {item.product_id}</p>
                      </div>
                      <div className="text-right flex-shrink-0 ml-4">
                        <p className="font-bold text-white">${parseFloat(item.price).toFixed(2)}</p>
                        <p className="text-xs text-slate-500">x{item.quantity}</p>
                      </div>
                    </div>
                  ))}
                  <div className="p-4 bg-slate-900 flex items-center justify-between text-sm font-bold text-white">
                    <span>Tổng tiền thanh toán</span>
                    <span className="text-lg text-indigo-400">${parseFloat(selectedOrder.total_amount).toFixed(2)}</span>
                  </div>
                </div>
              </div>

              {/* Status History */}
              {selectedOrder.status_history && selectedOrder.status_history.length > 0 && (
                <div className="space-y-2.5">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Lịch sử cập nhật trạng thái</h4>
                  <div className="space-y-2 pl-2 border-l-2 border-slate-800 ml-1.5">
                    {selectedOrder.status_history.map((hist, index) => (
                      <div key={index} className="relative pl-4 text-xs">
                        <div className="absolute left-[-13px] top-1.5 w-2 h-2 bg-indigo-500 rounded-full"></div>
                        <p className="font-semibold text-slate-300">
                          Trạng thái: <span className="text-indigo-400 uppercase font-bold">{getStatusDisplay(hist.status)}</span>
                        </p>
                        <p className="text-slate-500 mt-0.5">{hist.note}</p>
                        <p className="text-[10px] text-slate-600 mt-0.5">
                          {new Date(hist.created_at).toLocaleString('vi-VN')}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Status Update Note Input */}
              {selectedOrder.status !== 'delivered' && selectedOrder.status !== 'cancelled' && (
                <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 space-y-3">
                  <label className="block text-xs font-bold text-slate-400 uppercase">Ghi chú cập nhật trạng thái (Note)</label>
                  <input
                    type="text"
                    value={statusNote}
                    onChange={(e) => setStatusNote(e.target.value)}
                    placeholder="Nhập lý do hủy hoặc ghi chú vận chuyển..."
                    className="w-full px-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              )}
            </div>

            {/* Actions Footer */}
            <div className="h-20 bg-slate-950 border-t border-slate-800/80 px-6 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-500 font-semibold block uppercase">Trạng thái hiện tại</span>
                <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border uppercase tracking-wider ${getStatusBadgeClass(selectedOrder.status)}`}>
                  {getStatusDisplay(selectedOrder.status)}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                {/* Cancel action */}
                {selectedOrder.status !== 'delivered' && selectedOrder.status !== 'cancelled' && (
                  <button 
                    disabled={updatingStatus}
                    onClick={handleCancelOrder}
                    className="px-4 py-2 rounded-xl bg-rose-950/20 border border-rose-900/40 text-xs font-bold uppercase tracking-wider text-rose-400 hover:bg-rose-900/30 transition-all focus:outline-none disabled:opacity-50"
                  >
                    Hủy đơn hàng
                  </button>
                )}

                {/* Next Step Status actions */}
                {selectedOrder.status === 'pending' && (
                  <button 
                    disabled={updatingStatus}
                    onClick={() => handleUpdateStatus('confirmed')}
                    className="px-5 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold uppercase tracking-wider hover:bg-indigo-500 transition-all focus:outline-none disabled:opacity-50"
                  >
                    Xác nhận đơn
                  </button>
                )}

                {selectedOrder.status === 'confirmed' && (
                  <button 
                    disabled={updatingStatus}
                    onClick={() => handleUpdateStatus('processing')}
                    className="px-5 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold uppercase tracking-wider hover:bg-indigo-500 transition-all focus:outline-none disabled:opacity-50"
                  >
                    Bắt đầu xử lý
                  </button>
                )}

                {selectedOrder.status === 'processing' && (
                  <button 
                    disabled={updatingStatus}
                    onClick={() => handleUpdateStatus('shipping')}
                    className="px-5 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold uppercase tracking-wider hover:bg-indigo-500 transition-all focus:outline-none disabled:opacity-50"
                  >
                    Gửi vận chuyển
                  </button>
                )}

                {selectedOrder.status === 'shipping' && (
                  <button 
                    disabled={updatingStatus}
                    onClick={() => handleUpdateStatus('delivered')}
                    className="px-5 py-2 rounded-xl bg-emerald-600 text-white text-xs font-bold uppercase tracking-wider hover:bg-emerald-500 transition-all focus:outline-none disabled:opacity-50"
                  >
                    Hoàn tất giao hàng
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminOrdersPage;
