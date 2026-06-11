import { Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { addToWishlist, removeFromWishlist } from '../../store/slices/wishlistSlice';
import { setLoginModalOpen } from '../../store/slices/uiSlice';
import { Rate } from 'antd';
import { Heart } from 'lucide-react';
import toast from 'react-hot-toast';
import { formatPrice } from '../../utils/format';

const ProductCard = ({ product }) => {
  const dispatch = useDispatch();
  const { isAuthenticated } = useSelector((state) => state.auth);
  const { productIds: wishlistIds } = useSelector((state) => state.wishlist);

  const isInWishlist = wishlistIds.includes(product.id);

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
        .then(() => toast.success('Đã xóa khỏi yêu thích'))
        .catch((err) => toast.error(err));
    } else {
      dispatch(addToWishlist(product.id))
        .unwrap()
        .then(() => toast.success('Đã thêm vào yêu thích'))
        .catch((err) => toast.error(err));
    }
  };

  const primaryImage = product.primary_image?.image || product.image || '/placeholder.png';

  return (
    <Link 
      to={`/products/${product.id}`} 
      className="group bg-white rounded-lg border border-gray-100 overflow-hidden hover:shadow-lg transition-all duration-300 flex flex-col h-full cursor-pointer relative"
    >
      {/* Image Container */}
      <div className="relative aspect-square overflow-hidden bg-gray-50 rounded-t-lg">
        <img
          src={primaryImage}
          alt={product.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
        />
        {product.is_on_sale && product.discount_percent > 0 && (
          <span className="absolute top-2 left-2 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
            -{product.discount_percent}%
          </span>
        )}
        <button
          onClick={handleToggleWishlist}
          className={`absolute top-2 right-2 p-1.5 bg-white rounded-full shadow-md transition-all duration-300 ${
            isInWishlist ? 'opacity-100 text-red-500' : 'opacity-0 group-hover:opacity-100 hover:text-red-500 text-gray-400'
          }`}
        >
          <Heart className={`w-4 h-4 ${isInWishlist ? 'fill-current' : ''}`} />
        </button>
      </div>

      {/* Info Content */}
      <div className="p-3 flex-grow flex flex-col justify-between">
        <div>
          {/* Title */}
          <h3 className="text-sm text-gray-800 font-normal line-clamp-2 mb-1.5 h-10 group-hover:text-blue-600 transition-colors leading-relaxed">
            {product.name}
          </h3>

          {/* Rating & Sold Row */}
          <div className="flex items-center mb-2 flex-wrap gap-y-1">
            <Rate 
              disabled 
              allowHalf 
              defaultValue={parseFloat(product.rating_avg) || 5} 
              style={{ fontSize: 10 }} 
              className="text-yellow-400 flex items-center" 
            />
            <span className="text-xs text-gray-500 ml-1.5 border-l border-gray-200 pl-1.5 leading-none">
              Đã bán {product.sold_count >= 1000 ? `${(product.sold_count / 1000).toFixed(0)}k+` : product.sold_count || '100+'}
            </span>
          </div>
        </div>

        <div>
          {/* Price Row */}
          <div className="flex items-baseline gap-1.5 flex-wrap">
            <span className="text-red-500 font-bold text-base">
              {formatPrice(product.price)}
            </span>
            {product.compare_price && product.compare_price > product.price && (
              <span className="text-xs text-gray-400 line-through">
                {formatPrice(product.compare_price)}
              </span>
            )}
          </div>

          {/* Tiki-like Badges */}
          <div className="mt-2.5 pt-2 border-t border-gray-50 flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] text-blue-600 border border-blue-100 bg-blue-50 px-1 py-0.5 rounded font-medium">
              Chính hãng
            </span>
            <span className="text-[10px] text-green-600 border border-green-100 bg-green-50 px-1 py-0.5 rounded font-medium">
              Giao siêu tốc 2h
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
};

export default ProductCard;
