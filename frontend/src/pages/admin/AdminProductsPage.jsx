import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import productService from '../../services/productService';
import {
  PlusIcon,
  PencilSquareIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  FolderIcon,
  TagIcon,
  XMarkIcon,
  ShoppingBagIcon
} from '@heroicons/react/24/outline';

const AdminProductsPage = () => {
  // Tabs: 'products' | 'categories'
  const [activeTab, setActiveTab] = useState('products');

  // Product states
  const [products, setProducts] = useState([]);
  const [productsCount, setProductsCount] = useState(0);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState('');
  const [selectedStatusFilter, setSelectedStatusFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Category states
  const [categories, setCategories] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState({});

  // Modal/Form states
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [productForm, setProductForm] = useState({
    name: '',
    slug: '',
    description: '',
    short_description: '',
    sku: '',
    price: 0,
    compare_price: 0,
    cost_price: 0,
    category_id: '',
    brand: '',
    status: 'active',
    stock_quantity: 0,
    low_stock_threshold: 5,
    weight: 0,
    is_featured: false,
    image_url: '' // Mock primary image url
  });

  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    slug: '',
    description: '',
    parent: '',
    is_active: true,
    display_order: 0
  });

  // Load Initial Data
  useEffect(() => {
    fetchCategoriesData();
  }, []);

  useEffect(() => {
    if (activeTab === 'products') {
      fetchProductsData();
    }
  }, [activeTab, currentPage, selectedCategoryFilter, selectedStatusFilter]);

  const fetchCategoriesData = async () => {
    setLoadingCategories(true);
    try {
      const data = await productService.getCategories();
      setCategories(data || []);
    } catch (error) {
      console.error('Fetch categories error:', error);
      toast.error('Không thể tải danh sách danh mục');
    } finally {
      setLoadingCategories(false);
    }
  };

  const fetchProductsData = async () => {
    setLoadingProducts(true);
    try {
      const params = {
        page: currentPage,
        page_size: pageSize,
      };
      if (searchQuery.trim()) params.q = searchQuery; // Backend might handle search inside getProducts or query param
      if (selectedCategoryFilter) params.category = selectedCategoryFilter;
      if (selectedStatusFilter) params.status = selectedStatusFilter;

      const data = await productService.getProducts(params);
      setProducts(data.results || []);
      setProductsCount(data.count || 0);
    } catch (error) {
      console.error('Fetch products error:', error);
      toast.error('Không thể tải danh sách sản phẩm');
    } finally {
      setLoadingProducts(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchProductsData();
  };

  // Auto slug generation helper
  const generateSlug = (text) => {
    return text
      .toString()
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '') // Remove accents
      .replace(/[đĐ]/g, 'd')
      .replace(/([^a-z0-9\s])/g, '')
      .replace(/\s+/g, '-') // Replace spaces with -
      .replace(/-+/g, '-') // Remove duplicate -
      .trim();
  };

  const handleProductNameChange = (e) => {
    const name = e.target.value;
    setProductForm(prev => ({
      ...prev,
      name,
      slug: generateSlug(name)
    }));
  };

  const handleCategoryNameChange = (e) => {
    const name = e.target.value;
    setCategoryForm(prev => ({
      ...prev,
      name,
      slug: generateSlug(name)
    }));
  };

  // Open product form for edit/create
  const openProductForm = (product = null) => {
    if (product) {
      setEditingProduct(product);
      setProductForm({
        name: product.name || '',
        slug: product.slug || '',
        description: product.description || '',
        short_description: product.short_description || '',
        sku: product.sku || '',
        price: product.price || 0,
        compare_price: product.compare_price || 0,
        cost_price: product.cost_price || 0,
        category_id: product.category?.id || '',
        brand: product.brand || '',
        status: product.status || 'active',
        stock_quantity: product.stock_quantity || 0,
        low_stock_threshold: product.low_stock_threshold || 5,
        weight: product.weight || 0,
        is_featured: product.is_featured || false,
        image_url: product.primary_image?.image || ''
      });
    } else {
      setEditingProduct(null);
      setProductForm({
        name: '',
        slug: '',
        description: '',
        short_description: '',
        sku: '',
        price: 0,
        compare_price: 0,
        cost_price: 0,
        category_id: '',
        brand: '',
        status: 'active',
        stock_quantity: 0,
        low_stock_threshold: 5,
        weight: 0,
        is_featured: false,
        image_url: ''
      });
    }
    setIsProductModalOpen(true);
  };

  // Product Submit
  const handleProductSubmit = async (e) => {
    e.preventDefault();
    const loadingToast = toast.loading(editingProduct ? 'Đang cập nhật sản phẩm...' : 'Đang tạo sản phẩm mới...');
    try {
      // Mock images payload structure based on Serializer
      const payload = { ...productForm };
      
      // If mock image url is provided, we can simulate updating images list (not fully complex multipart, but matches standard backend fields)
      if (payload.image_url) {
        // In this implementation, the primary image will be saved if backend accepts it or we can handle it
        // We'll pass it in the form. Django serializer ignores extra fields or we can adapt
      }

      if (editingProduct) {
        await productService.updateProduct(editingProduct.id, payload);
        toast.success('Cập nhật sản phẩm thành công!', { id: loadingToast });
      } else {
        await productService.createProduct(payload);
        toast.success('Thêm sản phẩm thành công!', { id: loadingToast });
      }
      setIsProductModalOpen(false);
      fetchProductsData();
    } catch (error) {
      console.error('Submit product error:', error);
      toast.error(error.response?.data?.error || 'Có lỗi xảy ra khi lưu sản phẩm', { id: loadingToast });
    }
  };

  // Delete Product
  const handleDeleteProduct = async (id) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa sản phẩm này?')) return;

    const loadingToast = toast.loading('Đang xóa sản phẩm...');
    try {
      await productService.deleteProduct(id);
      toast.success('Xóa sản phẩm thành công', { id: loadingToast });
      fetchProductsData();
    } catch (error) {
      console.error('Delete product error:', error);
      toast.error('Không thể xóa sản phẩm', { id: loadingToast });
    }
  };

  // Open Category Form
  const openCategoryForm = () => {
    setCategoryForm({
      name: '',
      slug: '',
      description: '',
      parent: '',
      is_active: true,
      display_order: 0
    });
    setIsCategoryModalOpen(true);
  };

  // Category Submit
  const handleCategorySubmit = async (e) => {
    e.preventDefault();
    const loadingToast = toast.loading('Đang tạo danh mục mới...');
    try {
      const payload = { ...categoryForm };
      if (!payload.parent) delete payload.parent; // Remove blank parent UUID

      await productService.createCategory(payload);
      toast.success('Tạo danh mục mới thành công!', { id: loadingToast });
      setIsCategoryModalOpen(false);
      fetchCategoriesData();
    } catch (error) {
      console.error('Submit category error:', error);
      toast.error(error.response?.data?.error || 'Có lỗi xảy ra khi tạo danh mục', { id: loadingToast });
    }
  };

  // Delete Category
  const handleDeleteCategory = async (id) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa danh mục này? Tất cả danh mục con cũng sẽ bị ảnh hưởng.')) return;

    const loadingToast = toast.loading('Đang xóa danh mục...');
    try {
      await productService.deleteCategory(id);
      toast.success('Xóa danh mục thành công', { id: loadingToast });
      fetchCategoriesData();
    } catch (error) {
      console.error('Delete category error:', error);
      toast.error('Không thể xóa danh mục', { id: loadingToast });
    }
  };

  // Category Collapsible Tree Helpers
  const toggleCategoryExpand = (id) => {
    setExpandedCategories(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  // Render Recursive Category Items
  const renderCategoryNode = (category, depth = 0) => {
    const hasChildren = category.children && category.children.length > 0;
    const isExpanded = expandedCategories[category.id];

    return (
      <div key={category.id} className="select-none">
        <div 
          className="flex items-center justify-between py-3 px-4 hover:bg-slate-900/60 rounded-xl border border-slate-800/40 my-1.5 transition-colors"
          style={{ marginLeft: `${depth * 24}px` }}
        >
          <div className="flex items-center space-x-3 min-w-0">
            {hasChildren ? (
              <button 
                onClick={() => toggleCategoryExpand(category.id)}
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
              >
                {isExpanded ? <ChevronDownIcon className="w-4 h-4" /> : <ChevronRightIcon className="w-4 h-4" />}
              </button>
            ) : (
              <FolderIcon className="w-4 h-4 text-slate-600 flex-shrink-0" />
            )}
            <span className="font-semibold text-white truncate text-sm">{category.name}</span>
            <span className="text-slate-500 text-xs truncate">/{category.slug}</span>
            <span className="bg-slate-800 text-[10px] text-slate-400 px-2 py-0.5 rounded-full font-medium">
              {category.product_count || 0} sản phẩm
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <button 
              onClick={() => handleDeleteCategory(category.id)}
              className="p-1.5 rounded-lg text-rose-500 hover:bg-rose-950/20 hover:text-rose-400 transition-colors"
              title="Xóa danh mục"
            >
              <TrashIcon className="w-4.5 h-4.5" />
            </button>
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div className="border-l border-slate-800 ml-5.5 my-0.5 pl-1.5">
            {category.children.map(child => renderCategoryNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  // Helper to get flat categories list for dropdown options (recursive)
  const getFlatCategories = (cats, prefix = '') => {
    let list = [];
    cats.forEach(c => {
      list.push({ id: c.id, name: prefix + c.name });
      if (c.children && c.children.length > 0) {
        list = [...list, ...getFlatCategories(c.children, prefix + '— ')];
      }
    });
    return list;
  };

  const flatCategories = getFlatCategories(categories);

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800/80 shadow-xl flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-wide">Quản lý Catalog</h2>
          <p className="text-slate-400 text-sm mt-0.5">Quản trị danh mục sản phẩm, cấu hình biến thể và thêm sửa đổi kho hàng.</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="bg-slate-900 p-1 rounded-xl border border-slate-800 flex">
            <button 
              onClick={() => setActiveTab('products')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold tracking-wider uppercase transition-all duration-200 ${activeTab === 'products' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'}`}
            >
              Sản phẩm
            </button>
            <button 
              onClick={() => setActiveTab('categories')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold tracking-wider uppercase transition-all duration-200 ${activeTab === 'categories' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'}`}
            >
              Danh mục
            </button>
          </div>
          <button 
            onClick={activeTab === 'products' ? () => openProductForm() : openCategoryForm}
            className="flex items-center space-x-2 bg-indigo-600 text-white px-4 py-2.5 rounded-xl font-semibold text-xs tracking-wider uppercase hover:bg-indigo-500 hover:shadow-lg hover:shadow-indigo-600/20 transition-all focus:outline-none"
          >
            <PlusIcon className="w-4 h-4" />
            <span>Thêm {activeTab === 'products' ? 'Sản phẩm' : 'Danh mục'}</span>
          </button>
        </div>
      </div>

      {/* TAB 1: PRODUCTS TABLE */}
      {activeTab === 'products' && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/60 flex flex-col md:flex-row items-center justify-between gap-4">
            <form onSubmit={handleSearchSubmit} className="relative w-full md:max-w-xs">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm kiếm theo tên, SKU..."
                className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
              />
              <MagnifyingGlassIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-500" />
            </form>

            <div className="flex items-center gap-3 w-full md:w-auto">
              <div className="flex items-center space-x-2 bg-slate-900 px-3 py-2 rounded-xl border border-slate-800 w-full md:w-auto">
                <FunnelIcon className="w-4 h-4 text-slate-500" />
                <select
                  value={selectedCategoryFilter}
                  onChange={(e) => { setSelectedCategoryFilter(e.target.value); setCurrentPage(1); }}
                  className="bg-transparent text-xs text-slate-300 font-semibold focus:outline-none border-none pr-6 cursor-pointer"
                >
                  <option value="" className="bg-slate-900">Tất cả danh mục</option>
                  {flatCategories.map(cat => (
                    <option key={cat.id} value={cat.id} className="bg-slate-900">{cat.name}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center space-x-2 bg-slate-900 px-3 py-2 rounded-xl border border-slate-800 w-full md:w-auto">
                <TagIcon className="w-4 h-4 text-slate-500" />
                <select
                  value={selectedStatusFilter}
                  onChange={(e) => { setSelectedStatusFilter(e.target.value); setCurrentPage(1); }}
                  className="bg-transparent text-xs text-slate-300 font-semibold focus:outline-none border-none pr-6 cursor-pointer"
                >
                  <option value="" className="bg-slate-900">Tất cả trạng thái</option>
                  <option value="active" className="bg-slate-900">Đang bán (Active)</option>
                  <option value="draft" className="bg-slate-900">Nháp (Draft)</option>
                  <option value="archived" className="bg-slate-900">Đã lưu trữ (Archived)</option>
                </select>
              </div>

              <button 
                onClick={() => {
                  setSearchQuery('');
                  setSelectedCategoryFilter('');
                  setSelectedStatusFilter('');
                  setCurrentPage(1);
                }}
                className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors focus:outline-none"
                title="Làm mới bộ lọc"
              >
                <ArrowPathIcon className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Table Container */}
          <div className="bg-slate-950 rounded-2xl border border-slate-800/80 shadow-xl overflow-hidden">
            {loadingProducts ? (
              <div className="p-20 flex flex-col items-center justify-center space-y-4">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-indigo-500"></div>
                <p className="text-slate-400 text-sm">Đang tải danh sách sản phẩm...</p>
              </div>
            ) : products.length === 0 ? (
              <div className="p-20 text-center space-y-2">
                <ShoppingBagIcon className="w-12 h-12 text-slate-700 mx-auto" />
                <p className="text-slate-400 text-sm font-medium">Không tìm thấy sản phẩm nào</p>
                <p className="text-slate-500 text-xs">Hãy thay đổi bộ lọc hoặc thêm sản phẩm mới để bắt đầu.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-950 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      <th className="py-4 px-6">Sản phẩm</th>
                      <th className="py-4 px-6">SKU</th>
                      <th className="py-4 px-6">Danh mục</th>
                      <th className="py-4 px-6">Giá bán</th>
                      <th className="py-4 px-6">Tồn kho</th>
                      <th className="py-4 px-6">Trạng thái</th>
                      <th className="py-4 px-6 text-right">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-850">
                    {products.map((product) => (
                      <tr key={product.id} className="hover:bg-slate-900/35 transition-colors">
                        <td className="py-4 px-6">
                          <div className="flex items-center space-x-3.5">
                            <div className="w-11 h-11 bg-slate-900 rounded-lg flex items-center justify-center overflow-hidden border border-slate-800">
                              {product.primary_image ? (
                                <img src={product.primary_image.image} alt={product.name} className="w-full h-full object-cover" />
                              ) : (
                                <ShoppingBagIcon className="w-5.5 h-5.5 text-slate-600" />
                              )}
                            </div>
                            <div className="min-w-0">
                              <span className="font-semibold text-white text-sm block truncate hover:text-indigo-400 transition-colors cursor-pointer">
                                {product.name}
                              </span>
                              <span className="text-xs text-slate-500 font-medium truncate block max-w-[200px]">
                                {product.brand || 'No Brand'}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-6 font-mono text-xs text-slate-400 font-semibold">{product.sku || 'N/A'}</td>
                        <td className="py-4 px-6 text-sm text-slate-300 font-medium">{product.category_name || 'N/A'}</td>
                        <td className="py-4 px-6 text-sm font-bold text-white">
                          ${parseFloat(product.price).toFixed(2)}
                          {product.compare_price && parseFloat(product.compare_price) > 0 && (
                            <span className="text-[10px] text-slate-500 line-through block font-medium">
                              ${parseFloat(product.compare_price).toFixed(2)}
                            </span>
                          )}
                        </td>
                        <td className="py-4 px-6">
                          {product.stock_quantity <= 5 ? (
                            <span className="text-rose-400 font-bold text-xs bg-rose-950/20 px-2 py-0.5 rounded-full border border-rose-900/40">
                              {product.stock_quantity} (Ít hàng)
                            </span>
                          ) : (
                            <span className="text-slate-300 font-semibold text-sm">
                              {product.stock_quantity}
                            </span>
                          )}
                        </td>
                        <td className="py-4 px-6">
                          <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider border ${
                            product.status === 'active' 
                              ? 'bg-emerald-950/20 text-emerald-400 border-emerald-900/40' 
                              : product.status === 'draft'
                                ? 'bg-amber-950/20 text-amber-400 border-amber-900/40'
                                : 'bg-slate-900 text-slate-400 border-slate-800'
                          }`}>
                            {product.status}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-right">
                          <div className="flex items-center justify-end space-x-1.5">
                            <button 
                              onClick={() => openProductForm(product)}
                              className="p-1.5 rounded-lg text-indigo-400 hover:bg-indigo-950/25 hover:text-indigo-300 transition-colors"
                              title="Sửa sản phẩm"
                            >
                              <PencilSquareIcon className="w-5 h-5" />
                            </button>
                            <button 
                              onClick={() => handleDeleteProduct(product.id)}
                              className="p-1.5 rounded-lg text-rose-500 hover:bg-rose-950/25 hover:text-rose-400 transition-colors"
                              title="Xóa sản phẩm"
                            >
                              <TrashIcon className="w-5 h-5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {/* Pagination */}
                {productsCount > pageSize && (
                  <div className="py-4 px-6 border-t border-slate-800/80 flex items-center justify-between">
                    <span className="text-xs text-slate-400">
                      Hiển thị {products.length} trên {productsCount} sản phẩm
                    </span>
                    <div className="flex items-center space-x-1.5">
                      <button
                        onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={currentPage === 1}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-400 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800 transition-colors focus:outline-none"
                      >
                        Trước
                      </button>
                      <button
                        onClick={() => setCurrentPage(prev => (currentPage * pageSize < productsCount ? prev + 1 : prev))}
                        disabled={currentPage * pageSize >= productsCount}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-400 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800 transition-colors focus:outline-none"
                      >
                        Sau
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: CATEGORIES HIERARCHY */}
      {activeTab === 'categories' && (
        <div className="bg-slate-950 rounded-2xl border border-slate-800/80 shadow-xl p-6">
          {loadingCategories ? (
            <div className="p-20 flex flex-col items-center justify-center space-y-4">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-indigo-500"></div>
              <p className="text-slate-400 text-sm">Đang tải cấu trúc danh mục...</p>
            </div>
          ) : categories.length === 0 ? (
            <div className="p-20 text-center space-y-2">
              <FolderIcon className="w-12 h-12 text-slate-700 mx-auto" />
              <p className="text-slate-400 text-sm font-medium">Chưa có danh mục nào được khởi tạo</p>
              <button 
                onClick={openCategoryForm}
                className="mt-2 bg-indigo-600 text-white px-4 py-2 rounded-xl text-xs font-semibold hover:bg-indigo-500 transition-colors focus:outline-none"
              >
                Tạo danh mục gốc đầu tiên
              </button>
            </div>
          ) : (
            <div className="max-w-3xl">
              <h3 className="text-sm font-bold text-slate-400 mb-4 uppercase tracking-wider">Cơ cấu cây danh mục (Category Tree)</h3>
              <div className="space-y-1">
                {categories.map(cat => renderCategoryNode(cat))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============================================================
          PRODUCT MODAL (CREATE / EDIT)
          ============================================================ */}
      {isProductModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-end">
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity duration-300"
            onClick={() => setIsProductModalOpen(false)}
          />

          {/* Drawer Panel */}
          <div className="relative w-full max-w-2xl bg-slate-950 border-l border-slate-800 h-full flex flex-col justify-between shadow-2xl z-10 animate-slide-in">
            {/* Header */}
            <div className="h-16 flex items-center justify-between px-6 border-b border-slate-800/80 bg-slate-950">
              <h3 className="text-lg font-bold text-white">
                {editingProduct ? `Chỉnh sửa: ${editingProduct.name}` : 'Thêm sản phẩm mới'}
              </h3>
              <button 
                onClick={() => setIsProductModalOpen(false)}
                className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-900 transition-colors focus:outline-none"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>

            {/* Form Fields */}
            <form onSubmit={handleProductSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Tab 1: General Info */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider border-b border-slate-800/50 pb-1">1. Thông tin chung</h4>
                
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Tên sản phẩm *</label>
                  <input
                    type="text"
                    required
                    value={productForm.name}
                    onChange={handleProductNameChange}
                    placeholder="Ví dụ: Laptop Dell XPS 13"
                    className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Đường dẫn thân thiện (Slug)</label>
                    <input
                      type="text"
                      required
                      value={productForm.slug}
                      onChange={(e) => setProductForm(prev => ({ ...prev, slug: e.target.value }))}
                      placeholder="laptop-dell-xps-13"
                      className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Mã sản phẩm (SKU) *</label>
                    <input
                      type="text"
                      required
                      value={productForm.sku}
                      onChange={(e) => setProductForm(prev => ({ ...prev, sku: e.target.value }))}
                      placeholder="DELL-XPS-13-001"
                      className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Thương hiệu</label>
                    <input
                      type="text"
                      value={productForm.brand}
                      onChange={(e) => setProductForm(prev => ({ ...prev, brand: e.target.value }))}
                      placeholder="Dell"
                      className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Danh mục sản phẩm *</label>
                    <select
                      required
                      value={productForm.category_id}
                      onChange={(e) => setProductForm(prev => ({ ...prev, category_id: e.target.value }))}
                      className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                    >
                      <option value="">Chọn danh mục...</option>
                      {flatCategories.map(cat => (
                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Mô tả ngắn</label>
                  <input
                    type="text"
                    value={productForm.short_description}
                    onChange={(e) => setProductForm(prev => ({ ...prev, short_description: e.target.value }))}
                    placeholder="Mô tả tóm tắt tính năng sản phẩm"
                    className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Mô tả chi tiết</label>
                  <textarea
                    rows={4}
                    value={productForm.description}
                    onChange={(e) => setProductForm(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Mô tả đầy đủ chi tiết sản phẩm..."
                    className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
                  />
                </div>
              </div>

              {/* Tab 2: Pricing & Inventory */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider border-b border-slate-800/50 pb-1">2. Giá & Kho hàng</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Giá bán lẻ ($) *</label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      min="0"
                      value={productForm.price}
                      onChange={(e) => setProductForm(prev => ({ ...prev, price: parseFloat(e.target.value) || 0 }))}
                      className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Giá so sánh ($)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={productForm.compare_price}
                      onChange={(e) => setProductForm(prev => ({ ...prev, compare_price: parseFloat(e.target.value) || 0 }))}
                      className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Giá gốc nhập ($)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={productForm.cost_price}
                      onChange={(e) => setProductForm(prev => ({ ...prev, cost_price: parseFloat(e.target.value) || 0 }))}
                      className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Số lượng tồn kho *</label>
                    <input
                      type="number"
                      required
                      min="0"
                      value={productForm.stock_quantity}
                      onChange={(e) => setProductForm(prev => ({ ...prev, stock_quantity: parseInt(e.target.value) || 0 }))}
                      className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Ngưỡng báo sắp hết</label>
                    <input
                      type="number"
                      min="0"
                      value={productForm.low_stock_threshold}
                      onChange={(e) => setProductForm(prev => ({ ...prev, low_stock_threshold: parseInt(e.target.value) || 0 }))}
                      className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Trọng lượng (grams)</label>
                    <input
                      type="number"
                      min="0"
                      value={productForm.weight}
                      onChange={(e) => setProductForm(prev => ({ ...prev, weight: parseInt(e.target.value) || 0 }))}
                      className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>
              </div>

              {/* Tab 3: Images & Settings */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider border-b border-slate-800/50 pb-1">3. Đường dẫn Ảnh sản phẩm</h4>
                
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">URL Ảnh chính</label>
                  <input
                    type="url"
                    value={productForm.image_url}
                    onChange={(e) => setProductForm(prev => ({ ...prev, image_url: e.target.value }))}
                    placeholder="https://example.com/images/product-1.jpg"
                    className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  <div className="flex items-center space-x-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
                    <input
                      type="checkbox"
                      id="is_featured"
                      checked={productForm.is_featured}
                      onChange={(e) => setProductForm(prev => ({ ...prev, is_featured: e.target.checked }))}
                      className="w-4.5 h-4.5 rounded bg-slate-950 border-slate-800 text-indigo-600 focus:ring-indigo-500"
                    />
                    <label htmlFor="is_featured" className="text-xs font-bold text-slate-300 uppercase select-none cursor-pointer">Sản phẩm nổi bật (Featured)</label>
                  </div>

                  <div className="flex items-center space-x-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
                    <label className="text-xs font-bold text-slate-300 uppercase mr-3">Trạng thái bán</label>
                    <select
                      value={productForm.status}
                      onChange={(e) => setProductForm(prev => ({ ...prev, status: e.target.value }))}
                      className="flex-grow bg-slate-950 border border-slate-800 rounded-lg text-xs py-1 px-3 text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="active">Active (Đang bán)</option>
                      <option value="draft">Draft (Bản nháp)</option>
                      <option value="archived">Archived (Lưu trữ)</option>
                    </select>
                  </div>
                </div>
              </div>
            </form>

            {/* Footer buttons */}
            <div className="h-20 bg-slate-950 border-t border-slate-800/80 px-6 flex items-center justify-end space-x-3">
              <button 
                type="button"
                onClick={() => setIsProductModalOpen(false)}
                className="px-5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold tracking-wider uppercase text-slate-400 hover:text-white hover:bg-slate-800 transition-colors focus:outline-none"
              >
                Hủy
              </button>
              <button 
                onClick={handleProductSubmit}
                className="px-6 py-2.5 rounded-xl bg-indigo-600 text-white text-xs font-semibold tracking-wider uppercase hover:bg-indigo-500 hover:shadow-lg hover:shadow-indigo-600/20 transition-all focus:outline-none"
              >
                Lưu lại
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================
          CATEGORY MODAL (CREATE)
          ============================================================ */}
      {isCategoryModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity duration-300"
            onClick={() => setIsCategoryModalOpen(false)}
          />

          <div className="relative w-full max-w-md bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl z-10 overflow-hidden flex flex-col justify-between">
            <div className="h-16 flex items-center justify-between px-6 border-b border-slate-800/80">
              <h3 className="text-base font-bold text-white">Thêm danh mục mới</h3>
              <button 
                onClick={() => setIsCategoryModalOpen(false)}
                className="p-1 rounded-md text-slate-400 hover:text-white focus:outline-none"
              >
                <XMarkIcon className="w-5.5 h-5.5" />
              </button>
            </div>

            <form onSubmit={handleCategorySubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Tên danh mục *</label>
                <input
                  type="text"
                  required
                  value={categoryForm.name}
                  onChange={handleCategoryNameChange}
                  placeholder="Ví dụ: Thiết bị di động"
                  className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Đường dẫn thân thiện (Slug)</label>
                <input
                  type="text"
                  required
                  value={categoryForm.slug}
                  onChange={(e) => setCategoryForm(prev => ({ ...prev, slug: e.target.value }))}
                  placeholder="thiet-bi-di-dong"
                  className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Danh mục cha</label>
                <select
                  value={categoryForm.parent}
                  onChange={(e) => setCategoryForm(prev => ({ ...prev, parent: e.target.value }))}
                  className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="">Không có (Danh mục gốc)</option>
                  {flatCategories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase">Mô tả danh mục</label>
                <textarea
                  rows={3}
                  value={categoryForm.description}
                  onChange={(e) => setCategoryForm(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Mô tả tóm tắt về nhóm danh mục này..."
                  className="w-full px-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>
            </form>

            <div className="h-16 border-t border-slate-800/80 px-6 flex items-center justify-end space-x-3 bg-slate-950">
              <button 
                type="button"
                onClick={() => setIsCategoryModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-400 hover:text-white transition-colors focus:outline-none"
              >
                Hủy
              </button>
              <button 
                onClick={handleCategorySubmit}
                className="px-5 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-500 hover:shadow-lg transition-all focus:outline-none"
              >
                Lưu lại
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminProductsPage;
