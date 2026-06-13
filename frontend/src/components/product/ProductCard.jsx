import { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { addToWishlist, removeFromWishlist } from '../../store/slices/wishlistSlice';
import { setLoginModalOpen } from '../../store/slices/uiSlice';
import { Heart } from 'lucide-react';
import toast from 'react-hot-toast';
import { formatPrice } from '../../utils/format';

const ProductCard = ({ product: rawProduct }) => {
  const dispatch = useDispatch();
  const { isAuthenticated } = useSelector((state) => state.auth);
  const { productIds: wishlistIds } = useSelector((state) => state.wishlist);

  const product = rawProduct?.product || rawProduct?.data || rawProduct || {};

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

  const primaryImage = product.primary_image?.image || 
                       product.image || 
                       (product.images && product.images.length > 0 ? (product.images.find(img => img.is_primary)?.image || product.images[0]?.image) : null) || 
                       '/placeholder.png';

  // Quản lý fallback ảnh bằng state - tránh re-render loop
  const [imgSrc, setImgSrc] = useState(primaryImage || '/placeholder.png');
  const [imgFailed, setImgFailed] = useState(false);

  const handleImgError = useCallback(() => {
    if (!imgFailed) {
      setImgFailed(true);
      setImgSrc('/placeholder.png');
    }
  }, [imgFailed]);

  return (
    <Link 
      to={`/products/${product.id}`} 
      className="group flex flex-col bg-white rounded-lg overflow-hidden hover:shadow-custom-smooth transition-all duration-300 h-full cursor-pointer relative"
    >
      {/* Image Container */}
      <div className="relative aspect-[4/5] overflow-hidden bg-slate-50 flex items-center justify-center rounded-t-lg">
        <img
          src={imgSrc}
          alt={product.name}
          className="w-full h-full object-contain p-2 group-hover:scale-105 transition-transform duration-500"
          onError={handleImgError}
        />
        {product.is_on_sale && product.discount_percent > 0 && (
          <span className="absolute top-2 left-2 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
            -{product.discount_percent}%
          </span>
        )}
        <button
          onClick={handleToggleWishlist}
          className={`absolute top-2 right-2 p-1.5 bg-white rounded-full shadow-custom-smooth transition-all duration-300 ${
            isInWishlist ? 'opacity-100 text-red-500' : 'opacity-0 group-hover:opacity-100 hover:text-red-500 text-slate-400'
          }`}
        >
          <Heart className={`w-4 h-4 ${isInWishlist ? 'fill-current' : ''}`} />
        </button>
      </div>

      {/* Info Content */}
      <div className="p-4 flex-grow flex flex-col justify-between">
        <div>
          {/* Title */}
          <h3 className="text-sm text-slate-700 font-medium line-clamp-2 mb-1.5 h-10 group-hover:text-sky-400 transition-colors leading-relaxed">
            {product.name}
          </h3>

          {/* Rating & Sold Row - Only render if there is rating or sales */}
          {(parseFloat(product.rating_avg) > 0 || product.sold_count > 0) && (
            <div className="flex items-center mt-1.5 flex-wrap gap-y-1 text-[11px] text-slate-400">
              {parseFloat(product.rating_avg) > 0 && (
                <div className="flex items-center gap-0.5 mr-1.5">
                  <span className="text-amber-400">★</span>
                  <span className="font-semibold text-slate-700">{parseFloat(product.rating_avg).toFixed(1)}</span>
                </div>
              )}
              {product.sold_count > 0 && (
                <span className={`${parseFloat(product.rating_avg) > 0 ? 'border-l border-slate-200 pl-1.5' : ''} leading-none`}>
                  Đã bán {product.sold_count >= 1000 ? `${(product.sold_count / 1000).toFixed(0)}k+` : product.sold_count}
                </span>
              )}
            </div>
          )}
        </div>

        <div>
          {/* Price Row */}
          <div className="mt-2.5 flex items-baseline gap-1.5 flex-wrap">
            <span className="text-slate-900 font-semibold text-lg">
              {formatPrice(product.price)}
            </span>
            {product.compare_price && product.compare_price > product.price && (
              <span className="text-xs text-slate-400 line-through">
                {formatPrice(product.compare_price)}
              </span>
            )}
          </div>

          {/* Badges */}
          <div className="mt-3 pt-2.5 border-t border-slate-50 flex items-center gap-1.5 flex-wrap">
            <span className="text-[9px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded font-medium">
              Chính hãng
            </span>
            <span className="text-[9px] text-sky-500 bg-sky-50 px-1.5 py-0.5 rounded font-medium">
              Giao nhanh 2h
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
};

export default ProductCard;
