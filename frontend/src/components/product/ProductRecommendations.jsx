import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { recommendationService } from '../../services/aiService';
import { formatPrice } from '../../utils/format';
import { ShoppingCartIcon } from '@heroicons/react/24/solid';
import { useDispatch, useSelector } from 'react-redux';
import { addToCart } from '../../store/slices/cartSlice';
import { setLoginModalOpen } from '../../store/slices/uiSlice';
import toast from 'react-hot-toast';

const ProductRecommendations = ({
  productId = null,
  userId = null,
  type = 'similar', // 'similar', 'personalized', 'trending', 'bought_together'
  title = 'San pham goi y',
  limit = 6
}) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const dispatch = useDispatch();
  const { isAuthenticated } = useSelector((state) => state.auth);

  useEffect(() => {
    fetchRecommendations();
  }, [productId, userId, type]);

  const fetchRecommendations = async () => {
    setLoading(true);
    setError(null);

    try {
      let response;

      switch (type) {
        case 'similar':
          if (!productId) {
            setProducts([]);
            setLoading(false);
            return;
          }
          response = await recommendationService.getSimilar(productId, limit);
          break;

        case 'personalized':
          if (!userId) {
            // Fallback to trending if no user
            response = await recommendationService.getTrending(limit);
          } else {
            response = await recommendationService.getPersonalized(userId, limit);
          }
          break;

        case 'trending':
          response = await recommendationService.getTrending(limit);
          break;

        default:
          response = await recommendationService.getTrending(limit);
      }

      const data = response.data;
      // Handle different response formats
      const productList = data.products || data.recommendations || data.results || [];
      setProducts(productList);
    } catch (err) {
      console.error('Failed to fetch recommendations:', err);
      setError('Khong the tai goi y');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = (e, product) => {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      dispatch(setLoginModalOpen(true));
      return;
    }

    const pid = product.product_id || product.id;
    dispatch(addToCart({ productId: pid, quantity: 1 }))
      .unwrap()
      .then(() => toast.success('Da them vao gio hang'))
      .catch((err) => toast.error(err));
  };

  if (loading) {
    return (
      <div className="py-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[...Array(limit)].map((_, idx) => (
            <div key={idx} className="animate-pulse">
              <div className="bg-gray-200 aspect-square rounded-lg mb-2"></div>
              <div className="bg-gray-200 h-4 rounded mb-1"></div>
              <div className="bg-gray-200 h-4 w-2/3 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || products.length === 0) {
    return null;
  }

  return (
    <div className="py-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {type === 'similar' && (
          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
            AI Recommendation
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {products.slice(0, limit).map((product, idx) => {
          const data = product.data || product;
          const pid = product.product_id || product.id || data.id;
          const name = data.name || `Product ${pid}`;
          const price = data.price;
          const image = data.primary_image?.image || data.image || '/placeholder.png';
          const reason = product.reason;

          return (
            <Link
              key={idx}
              to={`/products/${pid}`}
              className="group bg-white rounded-lg border border-gray-100 overflow-hidden hover:shadow-md transition-shadow"
            >
              {/* Image */}
              <div className="aspect-square bg-gray-100 relative overflow-hidden">
                <img
                  src={image}
                  alt={name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  onError={(e) => {
                    e.target.src = '/placeholder.png';
                  }}
                />
                {product.score && (
                  <span className="absolute top-1 left-1 bg-blue-600 text-white text-xs px-1.5 py-0.5 rounded">
                    {Math.round(product.score * 100)}% match
                  </span>
                )}
              </div>

              {/* Content */}
              <div className="p-3">
                <h4 className="text-sm font-medium text-gray-900 line-clamp-2 group-hover:text-blue-600">
                  {name}
                </h4>

                {price && (
                  <p className="text-sm font-bold text-red-600 mt-1">
                    {formatPrice(price)}
                  </p>
                )}

                {reason && (
                  <p className="text-xs text-gray-500 mt-1 line-clamp-1">
                    {reason}
                  </p>
                )}

                {/* Add to cart button */}
                <button
                  onClick={(e) => handleAddToCart(e, product)}
                  className="mt-2 w-full bg-blue-600 text-white text-xs py-1.5 rounded flex items-center justify-center space-x-1 hover:bg-blue-700 transition-colors"
                >
                  <ShoppingCartIcon className="w-3 h-3" />
                  <span>Them vao gio</span>
                </button>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
};

export default ProductRecommendations;
