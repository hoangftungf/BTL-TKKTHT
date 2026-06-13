import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { recommendationService } from '../../services/aiService';
import ProductCard from './ProductCard';
import { staggerContainer, staggerItem } from '../../utils/animations';

const SkeletonShimmer = () => (
  <div className="space-y-4">
    <div className="h-6 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 rounded w-48 mb-4"
      style={{ backgroundSize: '200% 100%', animation: 'shimmer 1.5s ease-in-out infinite' }}
    />
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {[...Array(6)].map((_, idx) => (
        <div key={idx} className="animate-pulse">
          <motion.div
            className="bg-gray-200 aspect-square rounded-lg mb-2"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ repeat: Infinity, duration: 1.5, delay: idx * 0.1 }}
          />
          <div className="bg-gray-200 h-4 rounded mb-1"></div>
          <div className="bg-gray-200 h-4 w-2/3 rounded"></div>
        </div>
      ))}
    </div>
  </div>
);

const ProductRecommendations = ({
  productId = null,
  userId = null,
  type = 'similar',
  title = 'Sản phẩm gợi ý',
  limit = 6
}) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
    return <SkeletonShimmer />;
  }

  if (error || products.length === 0) {
    return null;
  }

  return (
    <motion.div
      className="py-2"
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
    >
      {title && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
      )}

      <motion.div
        className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4"
        variants={staggerContainer}
      >
        {products.slice(0, limit).map((product, idx) => {
          const pid = product.product_id || product.id || (product.product || product.data || product).id;
          return (
            <motion.div key={pid ?? idx} variants={staggerItem}>
              <ProductCard product={product} />
            </motion.div>
          );
        })}
      </motion.div>
    </motion.div>
  );
};

export default React.memo(ProductRecommendations);
