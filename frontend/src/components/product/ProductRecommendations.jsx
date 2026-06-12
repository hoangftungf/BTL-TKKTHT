import React, { useEffect, useState, useRef } from 'react';
import { recommendationService } from '../../services/aiService';
import ProductCard from './ProductCard';

const ProductRecommendations = ({
  productId = null,
  userId = null,
  type = 'similar', // 'similar', 'personalized', 'trending', 'bought_together'
  title = 'Sản phẩm gợi ý',
  limit = 6
}) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Dùng ref để theo dõi mount state, tránh setState sau khi unmount
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;

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
        const productList = data.products || data.recommendations || data.results || data.trending || [];

        // Chỉ cập nhật state nếu component vẫn còn mounted
        if (isMountedRef.current) {
          setProducts(productList);
        }
      } catch (err) {
        console.error('Failed to fetch recommendations:', err);
        if (isMountedRef.current) {
          setError('Không thể tải gợi ý');
          setProducts([]);
        }
      } finally {
        if (isMountedRef.current) {
          setLoading(false);
        }
      }
    };

    fetchRecommendations();

    return () => {
      isMountedRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId, userId, type, limit]);

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
    <div className="py-2">
      {title && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {products.slice(0, limit).map((product, idx) => {
          const pid = product.product_id || product.id || (product.product || product.data || product).id;
          return (
            <ProductCard
              key={pid ?? idx}
              product={product}
            />
          );
        })}
      </div>
    </div>
  );
};

export default React.memo(ProductRecommendations);
