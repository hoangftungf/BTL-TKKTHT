import ProductCard from './ProductCard';
import Loading from '../common/Loading';
import Empty from '../common/Empty';
import { CubeIcon } from '@heroicons/react/24/outline';

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
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
};

export default ProductGrid;
