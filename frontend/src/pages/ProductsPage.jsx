import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchProducts, fetchCategories } from '../store/slices/productSlice';
import ProductGrid from '../components/product/ProductGrid';
import { FunnelIcon, XMarkIcon } from '@heroicons/react/24/outline';

const ProductsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [showFilters, setShowFilters] = useState(false);
  const [priceFrom, setPriceFrom] = useState('');
  const [priceTo, setPriceTo] = useState('');
  const dispatch = useDispatch();

  const { products, categories, pagination, loading } = useSelector((state) => state.product);

  const currentCategory = searchParams.get('category') || '';
  const currentOrdering = searchParams.get('ordering') || '-created_at';
  const currentPage = searchParams.get('page') || '1';
  const minPrice = searchParams.get('min_price') || '';
  const maxPrice = searchParams.get('max_price') || '';

  useEffect(() => {
    dispatch(fetchCategories());
  }, [dispatch]);

  useEffect(() => {
    const params = {
      ordering: currentOrdering,
      page: currentPage,
    };

    if (currentCategory) {
      params.category = currentCategory;
    }
    if (minPrice) {
      params.min_price = minPrice;
    }
    if (maxPrice) {
      params.max_price = maxPrice;
    }

    dispatch(fetchProducts(params));
  }, [dispatch, currentCategory, currentOrdering, currentPage, minPrice, maxPrice]);

  const handleCategoryChange = (categoryId) => {
    if (categoryId) {
      searchParams.set('category', categoryId);
    } else {
      searchParams.delete('category');
    }
    setSearchParams(searchParams);
  };

  const orderingOptions = [
    { value: '-created_at', label: 'Mới nhất' },
    { value: 'price', label: 'Giá thấp đến cao' },
    { value: '-price', label: 'Giá cao đến thấp' },
    { value: '-sold_count', label: 'Bán chạy nhất' },
    { value: '-rating_avg', label: 'Đánh giá cao' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {currentCategory ? 'Danh mục sản phẩm' : 'Tất cả sản phẩm'}
        </h1>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="md:hidden btn-secondary flex items-center"
        >
          <FunnelIcon className="w-5 h-5 mr-2" />
          Lọc
        </button>
      </div>

      <div className="flex gap-8">
        {/* Filters Sidebar */}
        <aside className={`w-64 flex-shrink-0 ${showFilters ? 'block' : 'hidden'} md:block`}>
          <div className="card p-4 sticky top-24">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Bộ lọc</h3>
              <button onClick={() => setShowFilters(false)} className="md:hidden">
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>

            {/* Categories */}
            <div className="mb-6">
              <h4 className="font-medium text-gray-700 mb-2">Danh mục</h4>
              <div className="space-y-2">
                <button
                  onClick={() => handleCategoryChange('')}
                  className={`block w-full text-left px-3 py-2 rounded-lg text-sm ${
                    !currentCategory ? 'bg-primary-50 text-primary-600' : 'hover:bg-gray-100'
                  }`}
                >
                  Tất cả
                </button>
                {categories.map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => handleCategoryChange(cat.id)}
                    className={`block w-full text-left px-3 py-2 rounded-lg text-sm ${
                      currentCategory === String(cat.id) ? 'bg-primary-50 text-primary-600' : 'hover:bg-gray-100'
                    }`}
                  >
                    {cat.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Price Range */}
            <div className="mb-6">
              <h4 className="font-medium text-gray-700 mb-2">Khoảng giá</h4>
              <div className="flex items-center space-x-2 mb-2">
                <input
                  type="number"
                  placeholder="Từ"
                  value={priceFrom}
                  className="input text-sm"
                  onChange={(e) => setPriceFrom(e.target.value)}
                />
                <span>-</span>
                <input
                  type="number"
                  placeholder="Đến"
                  value={priceTo}
                  className="input text-sm"
                  onChange={(e) => setPriceTo(e.target.value)}
                />
              </div>
              <button
                onClick={() => {
                  if (priceFrom) searchParams.set('min_price', priceFrom);
                  else searchParams.delete('min_price');
                  if (priceTo) searchParams.set('max_price', priceTo);
                  else searchParams.delete('max_price');
                  searchParams.delete('page');
                  setSearchParams(searchParams);
                }}
                className="w-full btn-primary text-sm py-2"
              >
                Áp dụng
              </button>
            </div>
          </div>
        </aside>

        {/* Products Grid */}
        <div className="flex-grow">
          {/* Sorting */}
          <div className="flex items-center justify-between mb-4 bg-white p-4 rounded-lg shadow-sm">
            <p className="text-gray-600">
              {pagination.total} sản phẩm
            </p>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">Sắp xếp:</span>
              <select
                value={currentOrdering}
                onChange={(e) => {
                  searchParams.set('ordering', e.target.value);
                  setSearchParams(searchParams);
                }}
                className="input text-sm w-auto"
              >
                {orderingOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <ProductGrid products={products} loading={loading} />

          {/* Pagination */}
          {pagination.total > pagination.pageSize && (
            <div className="flex justify-center mt-8 space-x-2">
              {Array.from({ length: Math.ceil(pagination.total / pagination.pageSize) }, (_, i) => (
                <button
                  key={i + 1}
                  onClick={() => {
                    searchParams.set('page', i + 1);
                    setSearchParams(searchParams);
                  }}
                  className={`px-4 py-2 rounded-lg ${
                    pagination.page === i + 1
                      ? 'bg-primary-600 text-white'
                      : 'bg-white border hover:bg-gray-50'
                  }`}
                >
                  {i + 1}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductsPage;
