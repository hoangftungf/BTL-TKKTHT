import { motion, AnimatePresence } from 'framer-motion';
import ProductCard from './ProductCard';
import Loading from '../common/Loading';
import Empty from '../common/Empty';
import { CubeIcon } from '@heroicons/react/24/outline';
import { staggerContainer, staggerItem } from '../../utils/animations';

const ProductGrid = ({ products, loading, emptyMessage = 'Không tìm thấy sản phẩm' }) => {
  if (loading) {
    return <Loading />;
  }

  if (!products || products.length === 0) {
    return (
      <Empty
        icon={<CubeIcon className="w-16 h-16" />}
        title={emptyMessage}
        description="Vui lòng thử lại với từ khóa khác hoặc xem các sản phẩm khác."
      />
    );
  }

  return (
    <motion.div
      className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4"
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      layout
    >
      <AnimatePresence mode="popLayout">
        {products.map((product) => (
          <motion.div
            key={product.id}
            variants={staggerItem}
            layout
            exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
          >
            <ProductCard product={product} />
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  );
};

export default ProductGrid;
