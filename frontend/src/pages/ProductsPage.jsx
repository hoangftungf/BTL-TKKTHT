import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchProducts, fetchCategories } from '../store/slices/productSlice';
import ProductGrid from '../components/product/ProductGrid';
import { FunnelIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { 
  Smartphone, 
  Laptop, 
  Tablet, 
  Watch, 
  Trophy, 
  Home as HomeIcon, 
  BookOpen, 
  Sparkles, 
  Shirt, 
  Box
} from 'lucide-react';

const ProductsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [showFilters, setShowFilters] = useState(false);
  const [priceFrom, setPriceFrom] = useState('');
  const [priceTo, setPriceTo] = useState('');
  const dispatch = useDispatch();

  const { products, categories, subCategories, pagination, loading } = useSelector((state) => state.product);

  const currentCategory = searchParams.get('category') || '';
  const currentOrdering = searchParams.get('ordering') || '-created_at';
  const currentPage = searchParams.get('page') || '1';
  const minPrice = searchParams.get('min_price') || '';
  const maxPrice = searchParams.get('max_price') || '';

  useEffect(() => {
    dispatch(fetchCategories());
  }, [dispatch]);

  // Redirect to first parent category if no category is selected (Tiki/Shopee UX pattern)
  useEffect(() => {
    if (categories.length > 0 && !currentCategory) {
      searchParams.set('category', categories[0].id);
      setSearchParams(searchParams);
    }
  }, [categories, currentCategory, searchParams, setSearchParams]);

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
    searchParams.delete('page'); // Reset to page 1 on category change
    setSearchParams(searchParams);
  };

  const orderingOptions = [
    { value: '-created_at', label: 'Mới nhất' },
    { value: 'price', label: 'Giá thấp đến cao' },
    { value: '-price', label: 'Giá cao đến thấp' },
    { value: '-sold_count', label: 'Bán chạy nhất' },
    { value: '-rating_avg', label: 'Đánh giá cao' },
  ];

  // Map dynamic categories to icons
  const getCategoryIcon = (name) => {
    const n = name.toLowerCase();
    if (n.includes('thoại') || n.includes('phone')) return <Smartphone className="w-4 h-4 text-blue-500" />;
    if (n.includes('lap') || n.includes('máy tính')) return <Laptop className="w-4 h-4 text-blue-500" />;
    if (n.includes('bản') || n.includes('tablet')) return <Tablet className="w-4 h-4 text-blue-500" />;
    if (n.includes('đồng hồ') || n.includes('watch')) return <Watch className="w-4 h-4 text-blue-500" />;
    if (n.includes('thao') || n.includes('sport')) return <Trophy className="w-4 h-4 text-green-500" />;
    if (n.includes('dụng') || n.includes('nhà') || n.includes('home')) return <HomeIcon className="w-4 h-4 text-yellow-500" />;
    if (n.includes('sách') || n.includes('book')) return <BookOpen className="w-4 h-4 text-orange-500" />;
    if (n.includes('phẩm') || n.includes('mỹ') || n.includes('beauty')) return <Sparkles className="w-4 h-4 text-pink-500" />;
    if (n.includes('trang') || n.includes('fashion') || n.includes('áo') || n.includes('quần')) return <Shirt className="w-4 h-4 text-purple-500" />;
    return <Box className="w-4 h-4 text-gray-500" />;
  };

  // Find path of the current category (for Breadcrumbs and auto-expanding tree)
  const findCategoryPath = (categoryId, cats, currentPath = []) => {
    for (const cat of cats) {
      if (String(cat.id) === String(categoryId)) {
        return [...currentPath, cat];
      }
      if (cat.children) {
        const path = findCategoryPath(categoryId, cat.children, [...currentPath, cat]);
        if (path) return path;
      }
    }
    return null;
  };

  const categoryPath = currentCategory ? (findCategoryPath(currentCategory, categories) || []) : [];
  const currentCategoryName = categoryPath.length > 0 ? categoryPath[categoryPath.length - 1].name : null;

  // Recursive category tree renderer
  const renderCategoryTree = (cats, level = 0) => {
    return cats.map((cat) => {
      const isSelected = String(cat.id) === currentCategory;
      const isParentOfSelected = categoryPath.some(p => String(p.id) === String(cat.id));
      const hasChildren = cat.children && cat.children.length > 0;

      return (
        <div key={cat.id} className="space-y-1">
          <button
            onClick={() => handleCategoryChange(cat.id)}
            className={`flex items-center w-full text-left px-3 py-1.5 rounded-lg text-xs transition-colors ${
              isSelected 
                ? 'bg-blue-50 text-blue-600 font-bold' 
                : 'text-gray-700 hover:bg-gray-150'
            }`}
            style={{ paddingLeft: `${level * 12 + 12}px` }}
          >
            {level === 0 && (
              <span className="mr-2 flex-shrink-0">
                {getCategoryIcon(cat.name)}
              </span>
            )}
            {level > 0 && (
              <span className="mr-1.5 text-gray-400 font-semibold">•</span>
            )}
            <span className="truncate">{cat.name}</span>
          </button>
          
          {hasChildren && (isSelected || isParentOfSelected) && (
            <div className="space-y-1 mt-0.5">
              {renderCategoryTree(cat.children, level + 1)}
            </div>
          )}
        </div>
      );
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb Navigation */}
      <nav className="flex items-center space-x-2 text-xs text-gray-500 mb-6 overflow-x-auto whitespace-nowrap pb-2 scrollbar-none">
        <Link to="/" className="hover:text-blue-600 font-medium transition-colors">
          Trang chủ
        </Link>
        {categoryPath.map((cat, index) => {
          const isLast = index === categoryPath.length - 1;
          return (
            <span key={cat.id} className="flex items-center space-x-2">
              <span className="text-gray-400">/</span>
              {isLast ? (
                <span className="text-gray-800 font-bold truncate max-w-[150px]">
                  {cat.name}
                </span>
              ) : (
                <button
                  onClick={() => handleCategoryChange(cat.id)}
                  className="hover:text-blue-600 font-medium transition-colors truncate max-w-[150px]"
                >
                  {cat.name}
                </button>
              )}
            </span>
          );
        })}
      </nav>

      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">
          {currentCategoryName || 'Sản phẩm'}
        </h1>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="md:hidden btn-secondary flex items-center"
        >
          <FunnelIcon className="w-5 h-5 mr-2" />
          Lọc
        </button>
      </div>

      {/* Sub-categories Filter Tags */}
      {subCategories && subCategories.length > 0 && (
        <div className="mb-6">
          <div className="flex flex-wrap gap-2">
            {subCategories.map((subCat) => (
              <button
                key={subCat.id}
                onClick={() => handleCategoryChange(subCat.id)}
                className="px-4 py-2 rounded-full text-sm font-medium bg-white border border-gray-300 text-gray-700 hover:bg-primary-50 hover:border-primary-500 hover:text-primary-600 transition-colors"
              >
                {subCat.name}
              </button>
            ))}
          </div>
        </div>
      )}

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

            {/* Categories Tree */}
            <div className="mb-6">
              <h4 className="font-semibold text-gray-900 mb-3 px-1 text-sm flex items-center gap-2">
                <span className="w-1.5 h-4 bg-blue-600 rounded-full"></span>
                Danh mục
              </h4>
              <div className="space-y-1 max-h-[350px] overflow-y-auto pr-1 custom-scrollbar">
                {renderCategoryTree(categories)}
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
