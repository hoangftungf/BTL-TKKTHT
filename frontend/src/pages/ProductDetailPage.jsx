import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import { fetchProductById, clearCurrentProduct } from '../store/slices/productSlice';
import { addToCart } from '../store/slices/cartSlice';
import { addToWishlist, removeFromWishlist } from '../store/slices/wishlistSlice';
import { setLoginModalOpen, setCartDrawerOpen } from '../store/slices/uiSlice';
import Loading from '../components/common/Loading';
import ProductRecommendations from '../components/product/ProductRecommendations';
import { StarIcon, ShoppingCartIcon, MinusIcon, PlusIcon, TruckIcon, ShieldCheckIcon } from '@heroicons/react/24/solid';
import { HeartIcon as HeartOutline, ChevronRightIcon } from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolid } from '@heroicons/react/24/solid';
import { formatPrice } from '../utils/format';
import toast from 'react-hot-toast';
import reviewService from '../services/reviewService';
import { staggerContainer, staggerItem, fadeInUp } from '../utils/animations';

const ProductDetailPage = () => {
  const { id } = useParams();
  const dispatch = useDispatch();
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);
  const [mainImgFailed, setMainImgFailed] = useState(false);
  const [failedThumbnails, setFailedThumbnails] = useState({});
  const [selectedAttributes, setSelectedAttributes] = useState({});
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [activeTab, setActiveTab] = useState('desc');
  const [reviews, setReviews] = useState([]);
  const [reviewStats, setReviewStats] = useState(null);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [priceFlash, setPriceFlash] = useState(false);

  const toggleTab = (tabName) => {
    setActiveTab(prev => prev === tabName ? null : tabName);
  };

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

  useEffect(() => {
    if (product && product.id) {
      const loadReviews = async () => {
        setReviewsLoading(true);
        try {
          const [reviewsData, statsData] = await Promise.all([
            reviewService.getProductReviews(product.id),
            reviewService.getProductReviewStats(product.id)
          ]);
          setReviews(reviewsData);
          setReviewStats(statsData);
        } catch (error) {
          console.error("Failed to load reviews:", error);
        } finally {
          setReviewsLoading(false);
        }
      };
      loadReviews();
    }
  }, [product]);

  // Initialize selected attributes when product loads
  useEffect(() => {
    if (product && product.variants && product.variants.length > 0) {
      const initialVariant = product.variants.find(v => v.stock_quantity > 0 && v.is_active) || product.variants[0];
      if (initialVariant && initialVariant.attributes) {
        setSelectedAttributes(initialVariant.attributes);
      }
    } else {
      setSelectedAttributes({});
    }
  }, [product]);

  // Find matching variant when attributes selection changes
  useEffect(() => {
    if (product && product.variants && product.variants.length > 0) {
      const match = product.variants.find(variant => {
        if (!variant.attributes) return false;
        return Object.entries(selectedAttributes).every(([key, val]) => {
          return variant.attributes[key] === val;
        });
      });
      setSelectedVariant(match || null);
    } else {
      setSelectedVariant(null);
    }
  }, [selectedAttributes, product]);

  // Flash price when variant changes
  useEffect(() => {
    if (selectedVariant) {
      setPriceFlash(true);
      const timer = setTimeout(() => setPriceFlash(false), 600);
      return () => clearTimeout(timer);
    }
  }, [selectedVariant?.price]);

  // Sync selected image with selected variant color
  useEffect(() => {
    if (selectedVariant && product && product.images) {
      const color = selectedVariant.attributes?.color || selectedVariant.attributes?.['Màu sắc'] || selectedVariant.attributes?.['Màu'];
      if (color) {
        const matchingImgIndex = product.images.findIndex(img =>
          img.alt_text && img.alt_text.toLowerCase().includes(color.toLowerCase())
        );
        if (matchingImgIndex !== -1) {
          setSelectedImage(matchingImgIndex);
        }
      }
    }
  }, [selectedVariant, product]);

  // Compute unique values for each attribute key from all variants
  const attributeOptions = {};
  if (product && product.variants && product.variants.length > 0) {
    product.variants.forEach(variant => {
      if (variant.attributes && typeof variant.attributes === 'object') {
        Object.entries(variant.attributes).forEach(([key, val]) => {
          if (!attributeOptions[key]) {
            attributeOptions[key] = new Set();
          }
          attributeOptions[key].add(val);
        });
      }
    });
    Object.keys(attributeOptions).forEach(key => {
      attributeOptions[key] = Array.from(attributeOptions[key]);
    });
  }

  const getAttributeLabel = (key) => {
    const labels = {
      ram: 'RAM',
      ssd: 'SSD',
      color: 'Màu sắc',
      size: 'Kích cỡ',
      material: 'Chất liệu',
      storage: 'Dung lượng'
    };
    return labels[key.toLowerCase()] || key.charAt(0).toUpperCase() + key.slice(1);
  };

  const isOptionAvailable = (key, val) => {
    if (!product || !product.variants) return false;
    return product.variants.some(variant => {
      if (!variant.attributes || variant.stock_quantity <= 0 || !variant.is_active) return false;
      if (variant.attributes[key] !== val) return false;
      return Object.entries(selectedAttributes).every(([selKey, selVal]) => {
        if (selKey === key) return true;
        return variant.attributes[selKey] === selVal;
      });
    });
  };

  const handleAddToCart = () => {
    if (!isAuthenticated) {
      dispatch(setLoginModalOpen(true));
      return;
    }
    if (product.variants && product.variants.length > 0 && !selectedVariant) {
      toast.error('Vui lòng chọn đầy đủ thuộc tính sản phẩm');
      return;
    }
    const variantId = selectedVariant ? selectedVariant.id : null;
    dispatch(addToCart({ productId: product.id, quantity, variantId }))
      .unwrap()
      .then(() => {
        toast.success('Đã thêm vào giỏ hàng');
        dispatch(setCartDrawerOpen(true));
      })
      .catch((err) => toast.error(err));
  };

  const handleBuyNow = () => {
    if (!isAuthenticated) {
      dispatch(setLoginModalOpen(true));
      return;
    }
    if (product.variants && product.variants.length > 0 && !selectedVariant) {
      toast.error('Vui lòng chọn đầy đủ thuộc tính sản phẩm');
      return;
    }
    const variantId = selectedVariant ? selectedVariant.id : null;
    dispatch(addToCart({ productId: product.id, quantity, variantId }))
      .unwrap()
      .then(() => {
        dispatch(setCartDrawerOpen(true));
      })
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
        .then(() => toast.success('Đã xóa khỏi yêu thích'))
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

  const displayPrice = selectedVariant ? Number(selectedVariant.price) : Number(product.price);
  const displayComparePrice = selectedVariant
    ? (Number(selectedVariant.price) < Number(product.price) ? Number(product.price) : Number(product.compare_price))
    : Number(product.compare_price);
  const hasDiscount = displayComparePrice && displayComparePrice > displayPrice;
  const discountPercent = hasDiscount ? Math.round(((displayComparePrice - displayPrice) / displayComparePrice) * 100) : 0;
  const displayStock = selectedVariant ? selectedVariant.stock_quantity : product.stock_quantity;
  const displaySku = selectedVariant ? selectedVariant.sku : product.sku;

  return (
    <motion.div
      className="bg-slate-50 min-h-screen pb-12"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      {/* Breadcrumb */}
      <motion.div variants={staggerItem} className="bg-white border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center gap-1.5 text-xs text-slate-500">
          <Link to="/" className="hover:text-sky-400 transition-colors">Trang chủ</Link>
          <ChevronRightIcon className="w-3 h-3 text-slate-400" />
          {product.category_name && (
            <>
              <Link to="/products" className="hover:text-sky-400 transition-colors">{product.category_name}</Link>
              <ChevronRightIcon className="w-3 h-3 text-slate-400" />
            </>
          )}
          <span className="text-slate-800 font-medium line-clamp-1 max-w-[400px]">{product.name}</span>
        </div>
      </motion.div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Main Grid: 2 Columns */}
        <motion.div
          className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start mb-12"
          variants={staggerContainer}
        >
          {/* ===== CỘT TRÁI: GALLERY HÌNH ẢNH (Sticky) ===== */}
          <motion.div variants={staggerItem} className="lg:col-span-7 lg:sticky lg:top-24 space-y-4">
            <div className="relative aspect-square rounded-lg overflow-hidden bg-white border border-slate-100 flex items-center justify-center shadow-custom-smooth">
              <AnimatePresence mode="wait">
                <motion.img
                  key={selectedImage}
                  src={mainImgFailed ? '/placeholder.png' : (images[selectedImage]?.image || '/placeholder.png')}
                  alt={product.name}
                  className="w-full h-full object-contain p-4"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 1.05 }}
                  transition={{ duration: 0.25 }}
                  onError={() => setMainImgFailed(true)}
                />
              </AnimatePresence>
              {hasDiscount && (
                <div className="absolute top-4 left-4 bg-red-500 text-white text-xs font-bold px-2.5 py-1 rounded">
                  -{discountPercent}%
                </div>
              )}
              <motion.button
                onClick={handleToggleWishlist}
                className="absolute top-4 right-4 w-10 h-10 bg-white rounded-full shadow-custom-smooth border border-slate-100 flex items-center justify-center z-10"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                {isInWishlist
                  ? <HeartSolid className="w-5 h-5 text-red-500" />
                  : <HeartOutline className="w-5 h-5 text-slate-400" />
                }
              </motion.button>
            </div>

            {/* Thumbnails */}
            {images.length > 1 && (
              <div className="flex gap-3 overflow-x-auto py-1 scrollbar-none">
                {images.map((img, idx) => (
                  <motion.button
                    key={idx}
                    onClick={() => { setSelectedImage(idx); setMainImgFailed(false); }}
                    className={`w-20 h-20 flex-shrink-0 rounded-lg overflow-hidden bg-white border-2 transition-all p-1 flex items-center justify-center ${
                      selectedImage === idx
                        ? 'border-slate-900 shadow-sm'
                        : 'border-slate-200 hover:border-slate-400'
                    }`}
                    whileTap={{ scale: 0.95 }}
                  >
                    <img src={failedThumbnails[idx] ? '/placeholder.png' : (img.image || '/placeholder.png')} alt="" className="w-full h-full object-contain" onError={() => setFailedThumbnails(prev => ({ ...prev, [idx]: true }))} />
                  </motion.button>
                ))}
              </div>
            )}
          </motion.div>

          {/* ===== CỘT PHẢI: THÔNG TIN & CHỐT SALE ===== */}
          <motion.div variants={staggerItem} className="lg:col-span-5 space-y-6">
            {/* Badges */}
            <div className="flex flex-wrap items-center gap-2">
              {product.brand && (
                <span className="text-xs text-sky-400 font-semibold bg-sky-50 px-2.5 py-1 rounded">
                  Thương hiệu: {product.brand}
                </span>
              )}
              <span className="bg-emerald-50 text-emerald-700 text-[11px] font-bold px-2.5 py-1 rounded border border-emerald-100">
                ✓ CHÍNH HÃNG
              </span>
              {displayStock > 0 ? (
                <span className="bg-slate-100 text-slate-600 text-[11px] font-medium px-2.5 py-1 rounded">
                  Còn hàng ({displayStock})
                </span>
              ) : (
                <span className="bg-red-50 text-red-600 text-[11px] font-bold px-2.5 py-1 rounded">
                  Hết hàng
                </span>
              )}
            </div>

            {/* Product Title */}
            <h1 className="text-3xl font-display font-semibold text-slate-900 leading-snug">
              {product.name}
            </h1>

            {/* Rating row */}
            <div className="flex items-center gap-3 py-1 text-slate-500 text-sm">
              <div className="flex items-center gap-0.5">
                {[1, 2, 3, 4, 5].map((star) => (
                  <StarIcon
                    key={star}
                    className={`w-4 h-4 ${star <= Math.round(product.rating_avg) ? 'text-amber-400' : 'text-slate-200'}`}
                  />
                ))}
                <span className="text-sm font-semibold text-slate-800 ml-1">{Number(product.rating_avg || 0).toFixed(1)}</span>
              </div>
              <span className="text-slate-200">|</span>
              <span>{product.rating_count || 0} đánh giá</span>
              <span className="text-slate-200">|</span>
              <span>Đã bán <strong className="text-slate-700">{product.sold_count || 0}</strong></span>
            </div>

            {/* Price Block */}
            <motion.div
              className="border-t border-b border-slate-100 py-6"
              animate={priceFlash ? { backgroundColor: '#f0fdf4' } : { backgroundColor: 'transparent' }}
              transition={{ duration: 0.3 }}
            >
              <div className="flex items-baseline gap-4 flex-wrap">
                <motion.span
                  key={displayPrice}
                  initial={{ scale: 1.05, color: '#16a34a' }}
                  animate={{ scale: 1, color: '#0f172a' }}
                  className="text-4xl font-bold text-slate-900"
                >
                  {formatPrice(displayPrice)}
                </motion.span>
                {hasDiscount && (
                  <>
                    <span className="text-lg text-slate-400 line-through">{formatPrice(displayComparePrice)}</span>
                    <span className="bg-green-100 text-green-700 px-2 py-1 rounded-sm text-sm font-medium">
                      Tiết kiệm {discountPercent}%
                    </span>
                  </>
                )}
              </div>
              {displaySku && (
                <div className="text-xs text-slate-400 mt-2">
                  SKU: <span className="font-mono">{displaySku}</span>
                </div>
              )}
            </motion.div>

            {/* Chọn Biến Thể */}
            {product.variants && product.variants.length > 0 && (
              <div className="space-y-4">
                {Object.entries(attributeOptions).map(([key, options]) => (
                  <div key={key} className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block">
                      Chọn {getAttributeLabel(key)}:
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {options.map((val) => {
                        const isSelected = selectedAttributes[key] === val;
                        const isAvailable = isOptionAvailable(key, val);
                        return (
                          <motion.button
                            key={val}
                            disabled={!isAvailable}
                            onClick={() => setSelectedAttributes(prev => ({ ...prev, [key]: val }))}
                            className={`px-4 py-2 text-xs font-medium rounded-full border transition-all ${
                              isSelected
                                ? 'border-slate-900 border-2 bg-white text-slate-900 font-semibold'
                                : isAvailable
                                ? 'border-slate-200 bg-white text-slate-600 hover:border-slate-400'
                                : 'border-slate-100 bg-slate-50 text-slate-300 cursor-not-allowed line-through'
                            }`}
                            whileTap={isAvailable ? { scale: 0.95 } : undefined}
                          >
                            {val}
                          </motion.button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Quantity Selector */}
            {displayStock > 0 && (
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block">Số lượng:</label>
                <div className="flex items-center gap-3">
                  <div className="flex items-center border border-slate-200 rounded-md bg-white">
                    <motion.button
                      onClick={() => setQuantity(Math.max(1, quantity - 1))}
                      className="w-10 h-10 flex items-center justify-center text-slate-500 hover:text-slate-800 transition-colors"
                      whileTap={{ scale: 0.9 }}
                    >
                      <MinusIcon className="w-4 h-4" />
                    </motion.button>
                    <motion.span
                      key={quantity}
                      initial={{ scale: 1.3 }}
                      animate={{ scale: 1 }}
                      className="w-12 text-center text-sm font-semibold text-slate-800 select-none"
                    >
                      {quantity}
                    </motion.span>
                    <motion.button
                      onClick={() => setQuantity(Math.min(displayStock || 99, quantity + 1))}
                      className="w-10 h-10 flex items-center justify-center text-slate-500 hover:text-slate-800 transition-colors"
                      whileTap={{ scale: 0.9 }}
                    >
                      <PlusIcon className="w-4 h-4" />
                    </motion.button>
                  </div>
                  <span className="text-xs text-slate-400">({displayStock} sản phẩm có sẵn)</span>
                </div>
              </div>
            )}

            {/* CTA Buttons */}
            <div className="space-y-3 pt-2">
              <motion.button
                onClick={handleAddToCart}
                disabled={displayStock <= 0}
                className="w-full h-14 bg-slate-900 text-white rounded-md text-lg font-medium hover:bg-slate-800 transition-colors flex items-center justify-center gap-2 disabled:bg-slate-200 disabled:cursor-not-allowed disabled:text-slate-400 shadow-custom-smooth"
                whileHover={displayStock > 0 ? { scale: 1.01 } : undefined}
                whileTap={displayStock > 0 ? { scale: 0.99 } : undefined}
              >
                <ShoppingCartIcon className="w-5 h-5" />
                Thêm vào giỏ hàng
              </motion.button>
              <motion.button
                onClick={handleBuyNow}
                disabled={displayStock <= 0}
                className="w-full h-14 bg-white border-2 border-slate-900 text-slate-900 rounded-md text-lg font-medium hover:bg-slate-50 transition-colors disabled:border-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed"
                whileHover={displayStock > 0 ? { scale: 1.01 } : undefined}
                whileTap={displayStock > 0 ? { scale: 0.99 } : undefined}
              >
                Mua ngay
              </motion.button>
            </div>

            {/* Accordion Thông tin phụ */}
            <div className="border-t border-slate-100 pt-6">
              {product.description && (
                <div className="border-b border-slate-100 py-3.5">
                  <button
                    onClick={() => toggleTab('desc')}
                    className="flex justify-between items-center w-full text-slate-800 font-medium text-sm text-left focus:outline-none"
                  >
                    <span>Mô tả sản phẩm</span>
                    <span className="text-base text-slate-400">{activeTab === 'desc' ? '—' : '+'}</span>
                  </button>
                  <motion.div
                    initial={false}
                    animate={{
                      height: activeTab === 'desc' ? 'auto' : 0,
                      opacity: activeTab === 'desc' ? 1 : 0,
                    }}
                    transition={{ duration: 0.3, ease: 'easeInOut' }}
                    className="overflow-hidden"
                  >
                    <div className="mt-3 text-slate-500 text-sm leading-relaxed whitespace-pre-line max-h-96 overflow-y-auto">
                      {product.description}
                    </div>
                  </motion.div>
                </div>
              )}

              {product.specifications && Object.keys(product.specifications).length > 0 && (
                <div className="border-b border-slate-100 py-3.5">
                  <button
                    onClick={() => toggleTab('specs')}
                    className="flex justify-between items-center w-full text-slate-800 font-medium text-sm text-left focus:outline-none"
                  >
                    <span>Thông số kỹ thuật</span>
                    <span className="text-base text-slate-400">{activeTab === 'specs' ? '—' : '+'}</span>
                  </button>
                  <motion.div
                    initial={false}
                    animate={{
                      height: activeTab === 'specs' ? 'auto' : 0,
                      opacity: activeTab === 'specs' ? 1 : 0,
                    }}
                    transition={{ duration: 0.3, ease: 'easeInOut' }}
                    className="overflow-hidden"
                  >
                    <div className="mt-3">
                      <table className="w-full text-sm text-left text-slate-500 border border-slate-100 rounded-lg overflow-hidden">
                        <tbody>
                          {Object.entries(product.specifications).map(([key, val], idx) => (
                            <tr key={key} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                              <td className="px-4 py-2.5 font-medium text-slate-700 w-1/3 border-b border-slate-100">{key}</td>
                              <td className="px-4 py-2.5 text-slate-600 border-b border-slate-100">{String(val)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </motion.div>
                </div>
              )}

              <div className="border-b border-slate-100 py-3.5">
                <button
                  onClick={() => toggleTab('shipping')}
                  className="flex justify-between items-center w-full text-slate-800 font-medium text-sm text-left focus:outline-none"
                >
                  <span>Chính sách vận chuyển & Bảo hành</span>
                  <span className="text-base text-slate-400">{activeTab === 'shipping' ? '—' : '+'}</span>
                </button>
                <motion.div
                  initial={false}
                  animate={{
                    height: activeTab === 'shipping' ? 'auto' : 0,
                    opacity: activeTab === 'shipping' ? 1 : 0,
                  }}
                  transition={{ duration: 0.3, ease: 'easeInOut' }}
                  className="overflow-hidden"
                >
                  <div className="mt-3 space-y-3">
                    <div className="bg-slate-50 rounded-lg p-3 space-y-2.5 text-slate-600 text-xs">
                      <div className="flex items-start gap-2.5">
                        <TruckIcon className="w-4 h-4 text-slate-800 mt-0.5" />
                        <div>
                          <p className="font-semibold text-slate-800">Giao hàng hỏa tốc trong 2h</p>
                          <p className="mt-0.5">Hỗ trợ miễn phí vận chuyển lên đến 25k cho các đơn hàng từ 45k.</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-2.5">
                        <ShieldCheckIcon className="w-4 h-4 text-slate-800 mt-0.5" />
                        <div>
                          <p className="font-semibold text-slate-800">Bảo hành 12 tháng chính hãng</p>
                          <p className="mt-0.5">Cam kết 100% chính hãng. Hoàn tiền 200% nếu phát hiện hàng giả.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* Reviews & Ratings Section */}
        <motion.div
          variants={fadeInUp}
          className="bg-white rounded-lg shadow-custom-smooth border border-slate-100 p-6 mt-12"
        >
          <div className="flex items-center gap-2 mb-6 border-b border-slate-100 pb-4">
            <div className="w-1 h-6 bg-slate-900 rounded-full"></div>
            <h2 className="text-lg font-bold text-slate-900 font-display">Đánh giá từ khách hàng</h2>
          </div>

          {reviewsLoading ? (
            <div className="text-center py-8 text-slate-500 text-sm">Đang tải đánh giá...</div>
          ) : reviews.length === 0 ? (
            <div className="text-center py-12 bg-slate-50/50 rounded-lg border border-dashed border-slate-200">
              <p className="text-slate-500 text-sm">Chưa có đánh giá nào cho sản phẩm này.</p>
              <p className="text-xs text-slate-400 mt-1">Mua hàng và trở thành người đầu tiên đánh giá sản phẩm này!</p>
            </div>
          ) : (
            <div className="space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center bg-slate-50/50 p-6 rounded-xl border border-slate-100">
                <div className="md:col-span-4 text-center md:border-r md:border-slate-200/60 pb-6 md:pb-0">
                  <div className="text-5xl font-black text-slate-900 font-display">
                    {Number(reviewStats?.avg_rating || 0).toFixed(1)}
                  </div>
                  <div className="flex justify-center items-center gap-0.5 mt-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <StarIcon
                        key={star}
                        className={`w-5 h-5 ${star <= Math.round(reviewStats?.avg_rating || 0) ? 'text-amber-400' : 'text-slate-200'}`}
                      />
                    ))}
                  </div>
                  <p className="text-xs text-slate-500 mt-2 font-medium">
                    {reviewStats?.total_reviews || 0} nhận xét từ khách hàng
                  </p>
                </div>

                <div className="md:col-span-8 space-y-2.5">
                  {[5, 4, 3, 2, 1].map((stars) => {
                    const count = reviewStats?.rating_distribution?.[stars] || 0;
                    const total = reviewStats?.total_reviews || 1;
                    const percent = Math.round((count / total) * 100);
                    return (
                      <div key={stars} className="flex items-center gap-3 text-xs">
                        <span className="w-12 text-slate-600 font-medium">{stars} sao</span>
                        <div className="flex-1 h-2 bg-slate-200/80 rounded-full overflow-hidden">
                          <motion.div
                            className="h-full bg-amber-400 rounded-full"
                            initial={{ width: 0 }}
                            whileInView={{ width: `${percent}%` }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.8, delay: 0.1 }}
                          />
                        </div>
                        <span className="w-8 text-right text-slate-400 font-mono">{percent}%</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-6 divide-y divide-slate-100">
                {reviews.map((rev) => (
                  <motion.div
                    key={rev.id}
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.3 }}
                    className="pt-6 first:pt-0"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-sky-50 text-sky-600 border border-sky-100 flex items-center justify-center font-bold text-sm">
                          {rev.user_id ? String(rev.user_id).slice(0, 2).toUpperCase() : 'U'}
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-slate-900">
                            Khách hàng {rev.user_id ? `u-${String(rev.user_id).slice(0, 6)}` : 'ẩn danh'}
                          </p>
                          <p className="text-[11px] text-slate-400 mt-0.5">
                            {new Date(rev.created_at).toLocaleDateString('vi-VN')}
                          </p>
                        </div>
                      </div>
                      {rev.is_verified && (
                        <span className="text-[10px] text-emerald-700 font-bold bg-emerald-50 px-2 py-1 rounded border border-emerald-100 flex items-center gap-1">
                          ✓ Đã mua hàng
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-0.5 mt-3">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <StarIcon
                          key={star}
                          className={`w-4 h-4 ${star <= rev.rating ? 'text-amber-400' : 'text-slate-200'}`}
                        />
                      ))}
                    </div>

                    {rev.title && (
                      <h4 className="text-sm font-bold text-slate-950 mt-2.5">{rev.title}</h4>
                    )}
                    <p className="text-slate-650 text-sm mt-1.5 leading-relaxed whitespace-pre-line">{rev.content}</p>

                    {rev.replies && rev.replies.length > 0 && (
                      <div className="mt-4 ml-6 pl-4 border-l-2 border-sky-400 space-y-3 bg-sky-50/30 p-3.5 rounded-lg border border-sky-100/50">
                        {rev.replies.map((reply) => (
                          <div key={reply.id} className="text-xs">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-slate-900">
                                {reply.is_seller ? 'Phản hồi từ người bán' : 'Khách hàng'}
                              </span>
                              {reply.is_seller && (
                                <span className="bg-sky-500 text-white text-[9px] px-1.5 py-0.2 rounded-full font-bold">QTV</span>
                              )}
                              <span className="text-[10px] text-slate-400">{new Date(reply.created_at).toLocaleDateString('vi-VN')}</span>
                            </div>
                            <p className="text-slate-700 mt-1 leading-relaxed whitespace-pre-line">{reply.content}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </motion.div>

        {/* AI Recommendations */}
        <motion.div
          variants={fadeInUp}
          className="bg-white rounded-lg shadow-custom-smooth border border-slate-100 p-6 mt-12"
        >
          <div className="flex items-center gap-2 mb-5">
            <div className="w-1 h-6 bg-slate-900 rounded-full"></div>
            <h2 className="text-lg font-bold text-slate-900 font-display">Sản phẩm tương tự</h2>
            <span className="ml-auto text-xs bg-sky-50 text-sky-400 px-2.5 py-1 rounded-full font-semibold">✨ AI Gợi ý</span>
          </div>
          <ProductRecommendations
            productId={product.id}
            type="similar"
            title=""
            limit={6}
          />
        </motion.div>
      </div>
    </motion.div>
  );
};

export default ProductDetailPage;
