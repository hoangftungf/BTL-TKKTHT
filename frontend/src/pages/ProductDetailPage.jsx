import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchProductById, clearCurrentProduct } from '../store/slices/productSlice';
import { addToCart } from '../store/slices/cartSlice';
import { addToWishlist, removeFromWishlist } from '../store/slices/wishlistSlice';
import { setLoginModalOpen } from '../store/slices/uiSlice';
import Loading from '../components/common/Loading';
import ProductRecommendations from '../components/product/ProductRecommendations';
import { StarIcon, ShoppingCartIcon, MinusIcon, PlusIcon, TruckIcon, ShieldCheckIcon, CheckBadgeIcon, TagIcon } from '@heroicons/react/24/solid';
import { HeartIcon as HeartOutline, ChevronRightIcon } from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolid } from '@heroicons/react/24/solid';
import { formatPrice } from '../utils/format';
import toast from 'react-hot-toast';

const ProductDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);
  const [mainImgFailed, setMainImgFailed] = useState(false);
  const [failedThumbnails, setFailedThumbnails] = useState({});

  const { currentProduct: product, detailLoading: loading } = useSelector((state) => state.product);
  const { isAuthenticated } = useSelector((state) => state.auth);
  const { productIds: wishlistIds } = useSelector((state) => state.wishlist);

  const isInWishlist = product ? wishlistIds.includes(product.id) : false;

  useEffect(() => {
    dispatch(fetchProductById(id));
    window.scrollTo(0, 0);
    return () => {
      dispatch(clearCurrentProduct());
    };
  }, [dispatch, id]);

  const handleAddToCart = () => {
    if (!isAuthenticated) {
      dispatch(setLoginModalOpen(true));
      return;
    }
    dispatch(addToCart({ productId: product.id, quantity }))
      .unwrap()
      .then(() => toast.success('Đã thêm vào giỏ hàng'))
      .catch((err) => toast.error(err));
  };

  const handleBuyNow = () => {
    if (!isAuthenticated) {
      dispatch(setLoginModalOpen(true));
      return;
    }
    dispatch(addToCart({ productId: product.id, quantity }))
      .unwrap()
      .then(() => navigate('/cart'))
      .catch((err) => toast.error(err));
  };

  const handleToggleWishlist = () => {
    if (!isAuthenticated) {
      dispatch(setLoginModalOpen(true));
      return;
    }
    if (isInWishlist) {
      dispatch(removeFromWishlist(product.id))
        .unwrap()
        .then(() => toast.success('Đã xoá khỏi yêu thích'))
        .catch((err) => toast.error(err));
    } else {
      dispatch(addToWishlist(product.id))
        .unwrap()
        .then(() => toast.success('Đã thêm vào yêu thích'))
        .catch((err) => toast.error(err));
    }
  };

  if (loading || !product) {
    return <Loading />;
  }

  const images = product.images?.length > 0 ? product.images : [{ image: '/placeholder.png' }];
  const hasDiscount = product.compare_price && product.compare_price > product.price;

  return (
    <div className="bg-[#f5f5fa] min-h-screen">
      {/* Breadcrumb */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-[1200px] mx-auto px-4 py-2.5 flex items-center gap-1.5 text-xs text-gray-500">
          <Link to="/" className="hover:text-blue-600 transition-colors">Trang chủ</Link>
          <ChevronRightIcon className="w-3 h-3" />
          {product.category_name && (
            <>
              <Link to="/products" className="hover:text-blue-600 transition-colors">{product.category_name}</Link>
              <ChevronRightIcon className="w-3 h-3" />
            </>
          )}
          <span className="text-gray-700 font-medium line-clamp-1 max-w-[400px]">{product.name}</span>
        </div>
      </div>

      <div className="max-w-[1200px] mx-auto px-4 py-4">
        {/* Main card */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden mb-4">
          <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr_300px]">

            {/* ===== CỘT 1: HÌNH ẢNH ===== */}
            <div className="p-5 border-r border-gray-100">
              {/* Main image */}
              <div className="relative aspect-square rounded-xl overflow-hidden bg-gray-50 mb-3 group border border-gray-100">
                <img
                  src={mainImgFailed ? '/placeholder.png' : (images[selectedImage]?.image || '/placeholder.png')}
                  alt={product.name}
                  className="w-full h-full object-contain transition-transform duration-300 group-hover:scale-105"
                  onError={() => setMainImgFailed(true)}
                />
                {hasDiscount && (
                  <div className="absolute top-3 left-3 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                    -{product.discount_percent}%
                  </div>
                )}
                {/* Wishlist button */}
                <button
                  onClick={handleToggleWishlist}
                  className="absolute top-3 right-3 w-9 h-9 bg-white rounded-full shadow-md flex items-center justify-center hover:scale-110 transition-transform"
                >
                  {isInWishlist
                    ? <HeartSolid className="w-5 h-5 text-red-500" />
                    : <HeartOutline className="w-5 h-5 text-gray-400" />
                  }
                </button>
              </div>

              {/* Thumbnails */}
              {images.length > 1 && (
                <div className="flex gap-2 overflow-x-auto pb-1">
                  {images.map((img, idx) => (
                    <button
                      key={idx}
                      onClick={() => { setSelectedImage(idx); setMainImgFailed(false); }}
                      className={`w-16 h-16 flex-shrink-0 rounded-lg overflow-hidden border-2 transition-all ${
                        selectedImage === idx
                          ? 'border-blue-500 shadow-md scale-105'
                          : 'border-gray-200 hover:border-blue-300'
                      }`}
                    >
                      <img src={failedThumbnails[idx] ? '/placeholder.png' : (img.image || '/placeholder.png')} alt="" className="w-full h-full object-cover" onError={() => setFailedThumbnails(prev => ({ ...prev, [idx]: true }))} />
                    </button>
                  ))}
                </div>
              )}

              {/* Cam kết */}
              <div className="mt-4 bg-blue-50 rounded-xl p-3">
                <p className="text-xs font-semibold text-blue-800 mb-2 flex items-center gap-1">
                  <ShieldCheckIcon className="w-4 h-4" /> Xem thêm ưu điểm & lưu ý của sản phẩm
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { icon: '✅', text: '100% hàng thật' },
                    { icon: '🚚', text: 'Freeship mọi đơn' },
                    { icon: '🔄', text: 'Hoàn 200% nếu hàng giả' },
                    { icon: '🛡️', text: '30 ngày đổi trả' },
                  ].map((item) => (
                    <div key={item.text} className="flex items-center gap-1.5">
                      <span className="text-sm">{item.icon}</span>
                      <span className="text-[11px] text-blue-700 font-medium">{item.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* ===== CỘT 2: THÔNG TIN SẢN PHẨM ===== */}
            <div className="p-6 border-r border-gray-100">
              {/* Badges */}
              <div className="flex flex-wrap gap-2 mb-3">
                {product.brand && (
                  <span className="text-xs text-blue-600 font-semibold">
                    Thương hiệu: <span className="text-blue-500 underline cursor-pointer">{product.brand}</span>
                  </span>
                )}
                <span className="bg-green-100 text-green-700 text-[11px] font-bold px-2 py-0.5 rounded border border-green-200">
                  ✓ CHÍNH HÃNG
                </span>
                {product.stock_quantity > 0 && (
                  <span className="bg-blue-50 text-blue-600 text-[11px] font-medium px-2 py-0.5 rounded">
                    Còn hàng
                  </span>
                )}
              </div>

              {/* Product name */}
              <h1 className="text-[19px] font-semibold text-gray-900 leading-snug mb-3">
                {product.name}
              </h1>

              {/* Rating row */}
              <div className="flex flex-wrap items-center gap-3 mb-4 pb-4 border-b border-gray-100">
                <div className="flex items-center gap-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <StarIcon
                      key={star}
                      className={`w-4 h-4 ${star <= Math.round(product.rating_avg) ? 'text-yellow-400' : 'text-gray-200'}`}
                    />
                  ))}
                  <span className="text-sm font-semibold text-yellow-500 ml-1">{Number(product.rating_avg || 0).toFixed(1)}</span>
                </div>
                <span className="text-gray-300 text-xs">|</span>
                <span className="text-sm text-gray-500">{product.rating_count || 0} đánh giá</span>
                <span className="text-gray-300 text-xs">|</span>
                <span className="text-sm text-gray-500">Đã bán <strong className="text-gray-700">{product.sold_count || 0}</strong></span>
              </div>

              {/* Price block */}
              <div className="bg-[#fafafa] rounded-xl p-4 mb-5">
                <div className="flex items-baseline gap-3 flex-wrap">
                  <span className="text-3xl font-bold text-red-500">{formatPrice(product.price)}</span>
                  {hasDiscount && (
                    <>
                      <span className="text-base text-gray-400 line-through">{formatPrice(product.compare_price)}</span>
                      <span className="bg-red-100 text-red-600 text-xs font-bold px-2 py-0.5 rounded-full">
                        -{product.discount_percent}%
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Thông tin vận chuyển */}
              <div className="mb-5">
                <h3 className="font-semibold text-gray-800 mb-3">Thông tin vận chuyển</h3>
                <div className="space-y-3 bg-gray-50 rounded-xl p-4">
                  <div className="flex items-start gap-3">
                    <TruckIcon className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-800">Giao Thứ Ba</span>
                        <span className="text-xs text-gray-500">Trước 23:00 hôm nay</span>
                      </div>
                      <p className="text-xs text-green-600 font-medium mt-0.5">Freeship 10k đơn từ 45k, Freeship 25k đơn từ 100k</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <ShieldCheckIcon className="w-5 h-5 text-blue-500 flex-shrink-0" />
                    <span className="text-sm text-gray-700">Bảo hành chính hãng <strong>12 tháng</strong></span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-lg flex-shrink-0">🔄</span>
                    <span className="text-sm text-gray-700">Đổi trả trong <strong>30 ngày</strong> nếu sản phẩm lỗi</span>
                  </div>
                </div>
              </div>

              {/* Ưu đãi khác */}
              <div className="mb-5">
                <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <TagIcon className="w-4 h-4 text-orange-500" />
                  Ưu đãi khác
                </h3>
                <div className="flex flex-wrap gap-2">
                  <span className="border border-dashed border-red-300 bg-red-50 text-red-600 text-xs px-3 py-1.5 rounded-lg font-medium cursor-pointer hover:bg-red-100 transition-colors">
                    🎟 Giảm 20%
                  </span>
                  <span className="border border-dashed border-red-300 bg-red-50 text-red-600 text-xs px-3 py-1.5 rounded-lg font-medium cursor-pointer hover:bg-red-100 transition-colors">
                    🎟 Giảm 10%
                  </span>
                  <span className="border border-dashed border-orange-300 bg-orange-50 text-orange-600 text-xs px-3 py-1.5 rounded-lg font-medium cursor-pointer hover:bg-orange-100 transition-colors">
                    🎟 Freeship
                  </span>
                </div>
              </div>

              {/* Mô tả sản phẩm */}
              {product.description && (
                <div>
                  <h3 className="font-semibold text-gray-800 mb-3">Mô tả sản phẩm</h3>
                  <div className="text-sm text-gray-600 leading-relaxed whitespace-pre-line bg-gray-50 rounded-xl p-4 max-h-48 overflow-y-auto">
                    {product.description}
                  </div>
                </div>
              )}
            </div>

            {/* ===== CỘT 3: SIDEBAR MUA HÀNG ===== */}
            <div className="p-5 bg-white flex flex-col gap-4">
              {/* Seller info */}
              <div className="flex items-center gap-3 pb-4 border-b border-gray-100">
                <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-black text-sm">AI</span>
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="font-semibold text-sm text-gray-800">TikiAI Trading</span>
                    <CheckBadgeIcon className="w-4 h-4 text-blue-500" />
                  </div>
                  <div className="flex items-center gap-1 mt-0.5">
                    <StarIcon className="w-3 h-3 text-yellow-400" />
                    <span className="text-xs text-gray-500">4.7 · 5.5tr+ đánh giá</span>
                  </div>
                  <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded font-semibold">OFFICIAL</span>
                </div>
              </div>

              {/* Quantity */}
              <div>
                <label className="text-sm font-semibold text-gray-700 mb-2 block">Số Lượng</label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="w-9 h-9 border border-gray-300 rounded-lg flex items-center justify-center hover:bg-gray-100 hover:border-blue-400 transition-all active:scale-95"
                  >
                    <MinusIcon className="w-4 h-4 text-gray-600" />
                  </button>
                  <span className="w-12 text-center font-semibold text-lg text-gray-900">{quantity}</span>
                  <button
                    onClick={() => setQuantity(Math.min(product.stock_quantity || 99, quantity + 1))}
                    className="w-9 h-9 border border-gray-300 rounded-lg flex items-center justify-center hover:bg-gray-100 hover:border-blue-400 transition-all active:scale-95"
                  >
                    <PlusIcon className="w-4 h-4 text-gray-600" />
                  </button>
                  <span className="text-xs text-gray-400 ml-1">
                    ({product.stock_quantity ?? '—'} có sẵn)
                  </span>
                </div>
              </div>

              {/* Tạm tính */}
              <div className="bg-gray-50 rounded-xl p-3">
                <p className="text-xs text-gray-500 mb-1">Tạm tính</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatPrice(product.price * quantity)}
                </p>
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col gap-2.5">
                <button
                  onClick={handleBuyNow}
                  className="w-full py-3 bg-red-500 hover:bg-red-600 active:bg-red-700 text-white font-bold text-base rounded-xl transition-all shadow-sm hover:shadow-md active:scale-[0.98]"
                >
                  Mua ngay
                </button>
                <button
                  onClick={handleAddToCart}
                  className="w-full py-3 border-2 border-blue-500 text-blue-600 hover:bg-blue-50 font-bold text-base rounded-xl transition-all flex items-center justify-center gap-2 active:scale-[0.98]"
                >
                  <ShoppingCartIcon className="w-5 h-5" />
                  Thêm vào giỏ
                </button>
              </div>

              {/* Dịch vụ bổ sung */}
              <div className="border border-gray-200 rounded-xl p-3 space-y-2.5">
                <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Dịch vụ bổ sung</p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-[10px] font-bold">TC</span>
                    </div>
                    <span className="text-xs text-gray-700">Ưu đãi đến 600k với thẻ TikiCard</span>
                  </div>
                  <button className="text-xs text-blue-500 font-medium hover:underline">Đăng ký</button>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 bg-purple-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-[10px] font-bold">PL</span>
                    </div>
                    <span className="text-xs text-gray-700">Mua trước trả sau</span>
                  </div>
                  <button className="text-xs text-blue-500 font-medium hover:underline">Đăng ký</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* AI Recommendations - Similar Products */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-5">
            <div className="w-1 h-6 bg-blue-500 rounded-full"></div>
            <h2 className="text-lg font-bold text-gray-900">Sản phẩm tương tự</h2>
            <span className="ml-auto text-xs bg-blue-100 text-blue-700 px-2.5 py-1 rounded-full font-medium">✨ AI Gợi ý</span>
          </div>
          <ProductRecommendations
            productId={product.id}
            type="similar"
            title=""
            limit={6}
          />
        </div>
      </div>
    </div>
  );
};

export default ProductDetailPage;
