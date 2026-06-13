import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchOrderById, cancelOrder } from '../store/slices/orderSlice';
import Loading from '../components/common/Loading';
import { formatPrice, formatDateTime, formatOrderStatus, formatPaymentStatus, getStatusColor } from '../utils/format';
import toast from 'react-hot-toast';
import reviewService from '../services/reviewService';
import orderService from '../services/orderService';
import { StarIcon } from '@heroicons/react/24/solid';

const OrderDetailPage = () => {
  const { id } = useParams();
  const dispatch = useDispatch();
  const { currentOrder: order, loading } = useSelector((state) => state.order);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedItemToReview, setSelectedItemToReview] = useState(null);
  const [rating, setRating] = useState(5);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [orderReviews, setOrderReviews] = useState({});

  const openReviewModal = (item) => {
    setSelectedItemToReview(item);
    setRating(5);
    setTitle('');
    setContent('');
    setIsModalOpen(true);
  };

  const closeReviewModal = () => {
    setIsModalOpen(false);
    setSelectedItemToReview(null);
  };

  const loadOrderReviews = async () => {
    if (!order?.id) return;
    try {
      const reviewsData = await reviewService.getOrderReviews(order.id);
      const reviewsMap = {};
      reviewsData.forEach(r => {
        reviewsMap[r.product_id] = r;
      });
      setOrderReviews(reviewsMap);
    } catch (err) {
      console.error("Error fetching order reviews:", err);
    }
  };

  const handleSubmitReview = async () => {
    if (!content.trim() || rating === 0) return;
    setSubmittingReview(true);
    try {
      await reviewService.createReview({
        product_id: selectedItemToReview.product_id,
        order_id: order.id,
        rating,
        title,
        content
      });
      toast.success('Gửi đánh giá thành công! Cảm ơn ý kiến của bạn.');
      closeReviewModal();
      loadOrderReviews();
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.error || err.response?.data?.message || 'Có lỗi xảy ra khi gửi đánh giá');
    } finally {
      setSubmittingReview(false);
    }
  };

  useEffect(() => {
    dispatch(fetchOrderById(id));
  }, [dispatch, id]);

  useEffect(() => {
    loadOrderReviews();
  }, [order?.id]);

  const [confirmingReceived, setConfirmingReceived] = useState(false);

  const handleConfirmReceived = async () => {
    if (window.confirm('Xác nhận bạn đã nhận được đầy đủ hàng và muốn hoàn thành đơn hàng này?')) {
      setConfirmingReceived(true);
      try {
        await orderService.confirmReceived(order.id);
        toast.success('Xác nhận nhận hàng thành công!');
        dispatch(fetchOrderById(id));
      } catch (err) {
        console.error(err);
        toast.error(err.response?.data?.error || err.response?.data?.message || 'Có lỗi xảy ra khi xác nhận nhận hàng');
      } finally {
        setConfirmingReceived(false);
      }
    }
  };

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
  const canConfirmReceived = ['shipping', 'delivered'].includes(order.status);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <Link to="/orders" className="text-primary-600 hover:underline text-sm mb-2 inline-block">
            ← Quay lại đơn hàng
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Đơn hàng #{order.order_number}</h1>
        </div>
        <div className="flex items-center gap-3">
          {canConfirmReceived && (
            <button
              onClick={handleConfirmReceived}
              disabled={confirmingReceived}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold transition-all shadow-md active:scale-95 disabled:opacity-50"
            >
              {confirmingReceived ? 'Đang xác nhận...' : 'Đã nhận được hàng'}
            </button>
          )}
          {canCancel && (
            <button onClick={handleCancel} className="btn-danger">
              Hủy đơn hàng
            </button>
          )}
        </div>
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
                  <Link 
                    to={`/products/${item.product_id}`} 
                    className="w-20 h-20 rounded-lg bg-gray-100 overflow-hidden hover:opacity-90 transition-opacity flex-shrink-0"
                  >
                    <img src={item.product_image || '/placeholder.png'} alt="" className="w-full h-full object-cover" />
                  </Link>
                  <div className="flex-grow">
                    <Link 
                      to={`/products/${item.product_id}`} 
                      className="font-medium text-gray-900 hover:text-sky-500 hover:underline transition-colors"
                    >
                      {item.product_name}
                    </Link>
                    <p className="text-gray-500 text-sm mt-0.5">SKU: {item.sku}</p>
                    <p className="text-gray-500 text-sm">Số lượng: {item.quantity}</p>
                  </div>
                  <div className="flex flex-col items-end gap-2 max-w-[280px] sm:max-w-xs md:max-w-md w-full">
                    <p className="font-semibold text-right">{formatPrice(item.subtotal)}</p>
                    
                    {orderReviews[item.product_id] ? (
                      <div className="mt-1 p-3 bg-slate-50 border border-slate-100 rounded-lg w-full text-left shadow-sm">
                        <div className="flex items-center gap-1">
                          <span className="text-[11px] font-bold text-slate-800">Đã đánh giá:</span>
                          <div className="flex items-center gap-0.5 ml-1">
                            {[1, 2, 3, 4, 5].map((star) => (
                              <StarIcon
                                key={star}
                                className={`w-3 h-3 ${star <= orderReviews[item.product_id].rating ? 'text-amber-400' : 'text-slate-200'}`}
                              />
                            ))}
                          </div>
                        </div>
                        {orderReviews[item.product_id].title && (
                          <p className="text-[11px] font-bold text-slate-900 mt-1 line-clamp-1">{orderReviews[item.product_id].title}</p>
                        )}
                        <p className="text-[11px] text-slate-600 mt-0.5 italic break-words line-clamp-2">"{orderReviews[item.product_id].content}"</p>
                        
                        {/* Seller Replies */}
                        {orderReviews[item.product_id].replies && orderReviews[item.product_id].replies.length > 0 && (
                          <div className="mt-2 pl-2 border-l-2 border-sky-400 bg-sky-50/50 p-1.5 rounded text-[10px] space-y-1">
                            {orderReviews[item.product_id].replies.map((reply) => (
                              <div key={reply.id} className="break-words">
                                <span className="font-bold text-slate-800 block">Phản hồi của người bán:</span>
                                <p className="text-slate-600 mt-0.5 leading-relaxed">"{reply.content}"</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      order.status === 'completed' && (
                        <button
                          onClick={() => openReviewModal(item)}
                          className="px-3 py-1.5 bg-sky-500 hover:bg-sky-600 text-white rounded text-xs font-semibold shadow-sm transition-all"
                        >
                          Đánh giá sản phẩm
                        </button>
                      )
                    )}
                  </div>
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

      {/* Review Modal */}
      {isModalOpen && selectedItemToReview && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-lg w-full p-6 shadow-2xl border border-slate-100 relative">
            <button
              onClick={closeReviewModal}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 text-xl font-bold"
            >
              &times;
            </button>
            <h3 className="text-lg font-bold text-slate-900 mb-4 font-display">Viết đánh giá sản phẩm</h3>
            <div className="flex items-center gap-3 mb-4 p-3 bg-slate-50 rounded-lg">
              <img
                src={selectedItemToReview.product_image || '/placeholder.png'}
                alt=""
                className="w-12 h-12 object-cover rounded-md border border-slate-200"
              />
              <div>
                <p className="text-xs font-semibold text-slate-800 line-clamp-2">{selectedItemToReview.product_name}</p>
                <p className="text-[10px] text-slate-400 mt-0.5">SKU: {selectedItemToReview.sku}</p>
              </div>
            </div>
            
            <div className="space-y-4">
              {/* Rating stars */}
              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-1">
                  Chọn đánh giá sao
                </label>
                <div className="flex items-center gap-1.5">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      className="focus:outline-none"
                    >
                      <StarIcon
                        className={`w-8 h-8 transition-transform duration-150 active:scale-90 ${
                          star <= rating ? 'text-amber-400' : 'text-slate-200'
                        }`}
                      />
                    </button>
                  ))}
                </div>
              </div>

              {/* Title input */}
              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-1">
                  Tiêu đề đánh giá (Tùy chọn)
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Ví dụ: Sản phẩm rất tốt, đóng gói cẩn thận"
                  className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:outline-none focus:border-slate-800"
                />
              </div>

              {/* Content input */}
              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-1">
                  Nội dung bình luận
                </label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Hãy chia sẻ cảm nhận của bạn về sản phẩm này..."
                  rows={4}
                  required
                  className="w-full px-3 py-2 border border-slate-200 rounded-md text-sm focus:outline-none focus:border-slate-800 resize-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                type="button"
                onClick={closeReviewModal}
                disabled={submittingReview}
                className="px-4 py-2 border border-slate-200 rounded text-slate-600 text-sm font-semibold hover:bg-slate-50 disabled:opacity-50"
              >
                Hủy
              </button>
              <button
                type="button"
                onClick={handleSubmitReview}
                disabled={submittingReview || !content.trim() || rating === 0}
                className="px-4 py-2 bg-slate-900 text-white rounded text-sm font-semibold hover:bg-slate-800 disabled:opacity-50"
              >
                {submittingReview ? 'Đang gửi...' : 'Gửi đánh giá'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderDetailPage;
