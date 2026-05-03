import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchProductById, clearCurrentProduct } from '../store/slices/productSlice';
import { addToCart } from '../store/slices/cartSlice';
import { addToWishlist, removeFromWishlist } from '../store/slices/wishlistSlice';
import { setLoginModalOpen } from '../store/slices/uiSlice';
import Loading from '../components/common/Loading';
import ProductRecommendations from '../components/product/ProductRecommendations';
import { StarIcon, ShoppingCartIcon, MinusIcon, PlusIcon, TruckIcon, ShieldCheckIcon } from '@heroicons/react/24/solid';
import { HeartIcon as HeartOutline } from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolid } from '@heroicons/react/24/solid';
import { formatPrice } from '../utils/format';
import toast from 'react-hot-toast';

const ProductDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);

  const { currentProduct: product, loading } = useSelector((state) => state.product);
  const { isAuthenticated } = useSelector((state) => state.auth);
  const { productIds: wishlistIds } = useSelector((state) => state.wishlist);

  const isInWishlist = product ? wishlistIds.includes(product.id) : false;

  useEffect(() => {
    dispatch(fetchProductById(id));
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
        .then(() => toast.success('Da xoa khoi yeu thich'))
        .catch((err) => toast.error(err));
    } else {
      dispatch(addToWishlist(product.id))
        .unwrap()
        .then(() => toast.success('Da them vao yeu thich'))
        .catch((err) => toast.error(err));
    }
  };

  if (loading || !product) {
    return <Loading />;
  }

  const images = product.images?.length > 0 ? product.images : [{ image: '/placeholder.png' }];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="grid md:grid-cols-2 gap-8">
        {/* Images */}
        <div>
          <div className="aspect-square rounded-xl overflow-hidden bg-gray-100 mb-4">
            <img
              src={images[selectedImage]?.image}
              alt={product.name}
              className="w-full h-full object-cover"
            />
          </div>
          {images.length > 1 && (
            <div className="flex space-x-2 overflow-x-auto">
              {images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedImage(idx)}
                  className={`w-20 h-20 rounded-lg overflow-hidden flex-shrink-0 border-2 ${
                    selectedImage === idx ? 'border-primary-500' : 'border-transparent'
                  }`}
                >
                  <img src={img.image} alt="" className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Info */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{product.name}</h1>

          {/* Rating */}
          <div className="flex items-center space-x-4 mb-4">
            <div className="flex items-center">
              {[1, 2, 3, 4, 5].map((star) => (
                <StarIcon
                  key={star}
                  className={`w-5 h-5 ${
                    star <= product.rating_avg ? 'text-yellow-400' : 'text-gray-200'
                  }`}
                />
              ))}
              <span className="ml-2 text-gray-600">({product.rating_count} đánh giá)</span>
            </div>
            <span className="text-gray-400">|</span>
            <span className="text-gray-600">Đã bán {product.sold_count}</span>
          </div>

          {/* Price */}
          <div className="bg-gray-50 p-4 rounded-xl mb-6">
            <div className="flex items-baseline space-x-3">
              <span className="text-3xl font-bold text-red-600">{formatPrice(product.price)}</span>
              {product.compare_price && product.compare_price > product.price && (
                <>
                  <span className="text-lg text-gray-400 line-through">{formatPrice(product.compare_price)}</span>
                  <span className="badge-error">-{product.discount_percent}%</span>
                </>
              )}
            </div>
          </div>

          {/* Quantity */}
          <div className="mb-6">
            <label className="block text-gray-700 font-medium mb-2">Số lượng</label>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-100"
              >
                <MinusIcon className="w-5 h-5" />
              </button>
              <span className="w-16 text-center font-medium text-lg">{quantity}</span>
              <button
                onClick={() => setQuantity(quantity + 1)}
                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-100"
              >
                <PlusIcon className="w-5 h-5" />
              </button>
              <span className="text-gray-500 text-sm">
                {product.stock_quantity} sản phẩm có sẵn
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex space-x-4 mb-6">
            <button onClick={handleAddToCart} className="btn-outline flex-1 flex items-center justify-center">
              <ShoppingCartIcon className="w-5 h-5 mr-2" />
              Thêm vào giỏ
            </button>
            <button onClick={handleBuyNow} className="btn-primary flex-1">
              Mua ngay
            </button>
            <button
              onClick={handleToggleWishlist}
              className={`btn-secondary p-3 ${isInWishlist ? 'text-red-500 border-red-500' : ''}`}
            >
              {isInWishlist ? (
                <HeartSolid className="w-5 h-5" />
              ) : (
                <HeartOutline className="w-5 h-5 text-gray-400" />
              )}
            </button>
          </div>

          {/* Features */}
          <div className="border-t border-gray-200 pt-6 space-y-3">
            <div className="flex items-center text-gray-600">
              <TruckIcon className="w-5 h-5 text-primary-500 mr-3" />
              <span>Giao hàng miễn phí cho đơn từ 500.000đ</span>
            </div>
            <div className="flex items-center text-gray-600">
              <ShieldCheckIcon className="w-5 h-5 text-primary-500 mr-3" />
              <span>Bảo hành chính hãng 12 tháng</span>
            </div>
          </div>
        </div>
      </div>

      {/* Description */}
      <div className="mt-12">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Mo ta san pham</h2>
        <div className="card p-6 prose max-w-none">
          <p className="text-gray-700 whitespace-pre-line">{product.description}</p>
        </div>
      </div>

      {/* AI Recommendations - Similar Products */}
      <div className="mt-12 border-t border-gray-200">
        <ProductRecommendations
          productId={product.id}
          type="similar"
          title="San pham tuong tu"
          limit={6}
        />
      </div>

      {/* Trending Products */}
      <div className="border-t border-gray-200">
        <ProductRecommendations
          type="trending"
          title="San pham ban chay"
          limit={6}
        />
      </div>
    </div>
  );
};

export default ProductDetailPage;
