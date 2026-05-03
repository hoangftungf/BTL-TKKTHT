import { Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { addToCart } from '../../store/slices/cartSlice';
import { addToWishlist, removeFromWishlist } from '../../store/slices/wishlistSlice';
import { setLoginModalOpen } from '../../store/slices/uiSlice';
import { ShoppingCartIcon, StarIcon } from '@heroicons/react/24/solid';
import { HeartIcon as HeartOutline } from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolid } from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';
import { formatPrice } from '../../utils/format';

const ProductCard = ({ product }) => {
  const dispatch = useDispatch();
  const { isAuthenticated } = useSelector((state) => state.auth);
  const { productIds: wishlistIds } = useSelector((state) => state.wishlist);

  const isInWishlist = wishlistIds.includes(product.id);

  const handleAddToCart = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) {
      dispatch(setLoginModalOpen(true));
      return;
    }
    dispatch(addToCart({ productId: product.id, quantity: 1 }))
      .unwrap()
      .then(() => toast.success('Da them vao gio hang'))
      .catch((err) => toast.error(err));
  };

  const handleToggleWishlist = (e) => {
    e.preventDefault();
    e.stopPropagation();
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

  const primaryImage = product.primary_image?.image || '/placeholder.png';

  return (
    <Link to={`/products/${product.id}`} className="card group">
      {/* Image */}
      <div className="relative aspect-square overflow-hidden bg-gray-100">
        <img
          src={primaryImage}
          alt={product.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        />
        {product.is_on_sale && (
          <span className="absolute top-2 left-2 bg-red-500 text-white text-xs font-medium px-2 py-1 rounded">
            -{product.discount_percent}%
          </span>
        )}
        <button
          onClick={handleToggleWishlist}
          className={`absolute top-2 right-2 p-2 bg-white rounded-full shadow-md transition-all ${
            isInWishlist ? 'opacity-100 text-red-500' : 'opacity-0 group-hover:opacity-100 hover:text-red-500'
          }`}
        >
          {isInWishlist ? (
            <HeartSolid className="w-5 h-5" />
          ) : (
            <HeartOutline className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="font-medium text-gray-900 line-clamp-2 mb-2 group-hover:text-primary-600">
          {product.name}
        </h3>

        {/* Rating */}
        {product.rating_count > 0 && (
          <div className="flex items-center space-x-1 mb-2">
            <StarIcon className="w-4 h-4 text-yellow-400" />
            <span className="text-sm text-gray-600">
              {product.rating_avg} ({product.rating_count})
            </span>
          </div>
        )}

        {/* Price */}
        <div className="flex items-baseline space-x-2">
          <span className="text-lg font-bold text-red-600">
            {formatPrice(product.price)}
          </span>
          {product.compare_price && product.compare_price > product.price && (
            <span className="text-sm text-gray-400 line-through">
              {formatPrice(product.compare_price)}
            </span>
          )}
        </div>

        {/* Sold count */}
        {product.sold_count > 0 && (
          <p className="text-xs text-gray-500 mt-1">
            Đã bán {product.sold_count}
          </p>
        )}

        {/* Add to cart button */}
        <button
          onClick={handleAddToCart}
          className="mt-3 w-full btn-primary text-sm flex items-center justify-center space-x-2"
        >
          <ShoppingCartIcon className="w-4 h-4" />
          <span>Thêm vào giỏ</span>
        </button>
      </div>
    </Link>
  );
};

export default ProductCard;
