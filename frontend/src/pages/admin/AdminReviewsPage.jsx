import { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import reviewService from '../../services/reviewService';
import productService from '../../services/productService';
import { StarIcon } from '@heroicons/react/24/solid';
import { 
  EyeIcon, 
  EyeSlashIcon, 
  ChatBubbleLeftRightIcon, 
  ArrowPathIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const AdminReviewsPage = () => {
  const [allReviews, setAllReviews] = useState([]);
  const [products, setProducts] = useState([]);
  const [productsMap, setProductsMap] = useState({});
  const [loading, setLoading] = useState(true);

  // Filters
  const [productFilter, setProductFilter] = useState(''); // Selected product ID
  const [ratingFilter, setRatingFilter] = useState('');
  const [visibilityFilter, setVisibilityFilter] = useState('');
  const [productSearchQuery, setProductSearchQuery] = useState('');
  const [reviewSearchQuery, setReviewSearchQuery] = useState('');
  const [onlyShowWithReviews, setOnlyShowWithReviews] = useState(true);

  // Reply states
  const [replyTexts, setReplyTexts] = useState({});
  const [submittingReply, setSubmittingReply] = useState({});

  const loadData = async () => {
    setLoading(true);
    try {
      // Fetch products
      const prodRes = await productService.getProducts({ page_size: 500 });
      const items = prodRes.results || [];
      setProducts(items);
      const map = {};
      items.forEach(p => {
        map[p.id] = p;
      });
      setProductsMap(map);

      // Fetch reviews
      const reviewsData = await reviewService.adminGetReviews({});
      setAllReviews(reviewsData);
    } catch (err) {
      console.error(err);
      toast.error('Lỗi khi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleVisibility = async (reviewId, currentVisible) => {
    try {
      const updated = await reviewService.adminSetVisibility(reviewId, !currentVisible);
      setAllReviews(prev => prev.map(r => r.id === reviewId ? { ...r, is_visible: updated.is_visible } : r));
      toast.success(updated.is_visible ? 'Đã hiển thị đánh giá' : 'Đã ẩn đánh giá');
    } catch (err) {
      console.error(err);
      toast.error('Lỗi khi thay đổi trạng thái hiển thị');
    }
  };

  const handleReplyChange = (reviewId, text) => {
    setReplyTexts(prev => ({ ...prev, [reviewId]: text }));
  };

  const handleSubmitReply = async (reviewId) => {
    const content = replyTexts[reviewId];
    if (!content || !content.trim()) return;

    setSubmittingReply(prev => ({ ...prev, [reviewId]: true }));
    try {
      const reply = await reviewService.replyToReview(reviewId, content);
      setAllReviews(prev => prev.map(r => {
        if (r.id === reviewId) {
          const replies = r.replies ? [...r.replies, reply] : [reply];
          return { ...r, replies };
        }
        return r;
      }));
      setReplyTexts(prev => ({ ...prev, [reviewId]: '' }));
      toast.success('Gửi phản hồi thành công');
    } catch (err) {
      console.error(err);
      toast.error('Lỗi khi gửi phản hồi');
    } finally {
      setSubmittingReply(prev => ({ ...prev, [reviewId]: false }));
    }
  };

  // 1. Calculate general stats across all reviews (mapped per product)
  const stats = useMemo(() => {
    const counts = {};
    const sums = {};
    allReviews.forEach(r => {
      const pId = r.product_id;
      counts[pId] = (counts[pId] || 0) + 1;
      sums[pId] = (sums[pId] || 0) + r.rating;
    });

    const averages = {};
    Object.keys(sums).forEach(pId => {
      averages[pId] = (sums[pId] / counts[pId]).toFixed(1);
    });

    return { counts, averages };
  }, [allReviews]);

  // 2. Filter products list for sidebar selection
  const filteredProductsList = useMemo(() => {
    return products.filter(p => {
      const matchesSearch = p.name.toLowerCase().includes(productSearchQuery.toLowerCase());
      if (onlyShowWithReviews) {
        const count = stats.counts[p.id] || 0;
        return matchesSearch && count > 0;
      }
      return matchesSearch;
    }).sort((a, b) => {
      const countA = stats.counts[a.id] || 0;
      const countB = stats.counts[b.id] || 0;
      if (countB !== countA) return countB - countA; // Products with more reviews first
      return a.name.localeCompare(b.name);
    });
  }, [products, productSearchQuery, onlyShowWithReviews, stats]);

  // 3. Stats for currently selected product (or all products if empty)
  const activeProductStats = useMemo(() => {
    const filteredReviewsForStats = productFilter
      ? allReviews.filter(r => r.product_id === productFilter)
      : allReviews;

    const total = filteredReviewsForStats.length;
    const avg = total > 0 ? (filteredReviewsForStats.reduce((sum, r) => sum + r.rating, 0) / total).toFixed(1) : '0.0';
    
    const breakdown = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };
    filteredReviewsForStats.forEach(r => {
      breakdown[r.rating] = (breakdown[r.rating] || 0) + 1;
    });

    return { total, avg, breakdown };
  }, [allReviews, productFilter]);

  // 4. Get active filtered reviews list to display
  const filteredReviews = useMemo(() => {
    return allReviews.filter(r => {
      if (productFilter && r.product_id !== productFilter) return false;
      if (ratingFilter && r.rating !== parseInt(ratingFilter)) return false;
      if (visibilityFilter !== '') {
        const isVis = visibilityFilter === 'true';
        if (r.is_visible !== isVis) return false;
      }
      if (reviewSearchQuery) {
        const q = reviewSearchQuery.toLowerCase();
        const contentMatch = r.content?.toLowerCase().includes(q);
        const titleMatch = r.title?.toLowerCase().includes(q);
        const userMatch = String(r.user_id).toLowerCase().includes(q);
        const orderMatch = r.order_id && String(r.order_id).toLowerCase().includes(q);
        if (!contentMatch && !titleMatch && !userMatch && !orderMatch) return false;
      }
      return true;
    }).sort((a, b) => new Date(b.created_at) - new Date(a.created_at)); // Newest first
  }, [allReviews, productFilter, ratingFilter, visibilityFilter, reviewSearchQuery]);

  const selectedProduct = productFilter ? productsMap[productFilter] : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white font-display">Quản lý đánh giá</h2>
          <p className="text-xs text-slate-400 mt-1">Xem, ẩn/hiển thị và phản hồi các đánh giá của khách hàng</p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center justify-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-medium transition-colors border border-slate-700"
        >
          <ArrowPathIcon className="w-4 h-4" />
          Tải lại
        </button>
      </div>

      {loading ? (
        <div className="text-center py-24 text-slate-400 text-sm flex flex-col items-center justify-center gap-3">
          <ArrowPathIcon className="w-8 h-8 animate-spin text-indigo-500" />
          <span>Đang tải danh sách đánh giá...</span>
        </div>
      ) : (
        <div className="flex flex-col lg:flex-row gap-6">
          
          {/* Sidebar / Left Column: Products Selector */}
          <div className="w-full lg:w-80 shrink-0 space-y-4">
            
            {/* Header info / Search */}
            <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Bộ lọc sản phẩm</h3>
                <span className="text-[10px] text-slate-500 font-medium">Tìm thấy {filteredProductsList.length}</span>
              </div>
              
              <div className="relative">
                <input
                  type="text"
                  value={productSearchQuery}
                  onChange={(e) => setProductSearchQuery(e.target.value)}
                  placeholder="Tìm kiếm sản phẩm..."
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-slate-650 placeholder:italic"
                />
                <MagnifyingGlassIcon className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              </div>

              <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={onlyShowWithReviews}
                  onChange={(e) => setOnlyShowWithReviews(e.target.checked)}
                  className="rounded bg-slate-900 border-slate-800 text-indigo-650 focus:ring-0 focus:ring-offset-0 w-3.5 h-3.5"
                />
                <span>Chỉ hiện sản phẩm có đánh giá</span>
              </label>
            </div>

            {/* Mobile horizontal scroll of product selectors */}
            <div className="flex lg:hidden overflow-x-auto gap-2 pb-2 -mx-4 px-4 scrollbar-none">
              <button
                onClick={() => setProductFilter('')}
                className={`shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-semibold whitespace-nowrap transition-all ${
                  productFilter === ''
                    ? 'bg-indigo-600 border-indigo-500 text-white'
                    : 'bg-slate-900 border-slate-800 text-slate-350 hover:bg-slate-800/50'
                }`}
              >
                Tất cả sản phẩm ({allReviews.length})
              </button>
              {filteredProductsList.map(p => (
                <button
                  key={p.id}
                  onClick={() => setProductFilter(p.id)}
                  className={`shrink-0 flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-semibold whitespace-nowrap transition-all ${
                    productFilter === p.id
                      ? 'bg-indigo-600 border-indigo-500 text-white'
                      : 'bg-slate-900 border-slate-800 text-slate-350 hover:bg-slate-800/50'
                  }`}
                >
                  <img
                    src={p.primary_image?.image || p.image || '/placeholder.png'}
                    alt={p.name}
                    className="w-5 h-5 object-cover rounded-md border border-slate-800 bg-slate-950"
                  />
                  <span>{p.name.length > 20 ? p.name.slice(0, 20) + '...' : p.name}</span>
                  <span className="text-[10px] text-slate-500 bg-slate-950/40 px-1.5 py-0.5 rounded border border-slate-800/40">
                    {stats.counts[p.id] || 0}
                  </span>
                </button>
              ))}
            </div>

            {/* Desktop vertical list of product selectors */}
            <div className="hidden lg:flex flex-col gap-2 max-h-[600px] overflow-y-auto pr-1 custom-scrollbar">
              <button
                onClick={() => setProductFilter('')}
                className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all border text-left ${
                  productFilter === ''
                    ? 'bg-indigo-600/15 border-indigo-500 text-white shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]'
                    : 'bg-slate-950/20 border-slate-800/60 hover:bg-slate-900/30 text-slate-300'
                }`}
              >
                <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold shrink-0 text-sm">
                  ALL
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-bold text-slate-200">Tất cả sản phẩm</h4>
                  <p className="text-[11px] text-slate-400 mt-1">{allReviews.length} đánh giá tổng cộng</p>
                </div>
              </button>

              {filteredProductsList.map(p => (
                <button
                  key={p.id}
                  onClick={() => setProductFilter(p.id)}
                  className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all border text-left ${
                    productFilter === p.id
                      ? 'bg-indigo-600/15 border-indigo-500 text-white shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]'
                      : 'bg-slate-950/20 border-slate-800/60 hover:bg-slate-900/30 text-slate-300'
                  }`}
                >
                  <img
                    src={p.primary_image?.image || p.image || '/placeholder.png'}
                    alt={p.name}
                    className="w-10 h-10 object-cover rounded-lg border border-slate-800 shrink-0 bg-slate-900"
                  />
                  <div className="min-w-0 flex-1">
                    <h4 className="text-xs font-bold text-slate-200 truncate">{p.name}</h4>
                    <div className="flex items-center gap-1.5 mt-1 text-[11px]">
                      <div className="flex items-center text-amber-400 font-bold">
                        <StarIcon className="w-3.5 h-3.5 fill-current" />
                        <span className="ml-0.5">{stats.averages[p.id] || '0.0'}</span>
                      </div>
                      <span className="text-slate-700">•</span>
                      <span className="text-slate-400 font-medium">{stats.counts[p.id] || 0} đánh giá</span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Right Column: Active Header + Reviews Grid */}
          <div className="flex-1 space-y-6">
            
            {/* Header / Summary Card */}
            {selectedProduct ? (
              <div className="bg-slate-950/40 border border-slate-800/80 rounded-2xl p-5 flex flex-col md:flex-row gap-5 items-start md:items-center">
                <img
                  src={selectedProduct.primary_image?.image || selectedProduct.image || '/placeholder.png'}
                  alt={selectedProduct.name}
                  className="w-20 h-20 object-cover rounded-xl border border-slate-800 shrink-0 bg-slate-900"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[9px] uppercase tracking-wider font-bold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded">
                      Chi tiết sản phẩm
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">ID: {selectedProduct.id}</span>
                  </div>
                  <h3 className="text-base font-bold text-white mt-1 hover:text-indigo-400 transition-colors truncate">
                    <Link to={`/products/${selectedProduct.id}`} target="_blank">
                      {selectedProduct.name}
                    </Link>
                  </h3>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-1">{selectedProduct.description}</p>
                  <div className="flex items-center gap-3 mt-2 flex-wrap text-xs text-slate-350">
                    <div>
                      Giá: <span className="text-emerald-400 font-bold">{new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(selectedProduct.price)}</span>
                    </div>
                    <span className="text-slate-700">|</span>
                    <div>
                      Danh mục: <span className="text-indigo-300 font-medium">{selectedProduct.category_name || 'Mặc định'}</span>
                    </div>
                  </div>
                </div>
                
                {/* Stats block */}
                <div className="w-full md:w-56 bg-slate-900/40 p-3 rounded-xl border border-slate-800/80 flex gap-3 items-center shrink-0">
                  <div className="text-center shrink-0 w-16">
                    <div className="text-2xl font-extrabold text-white leading-none">{activeProductStats.avg}</div>
                    <div className="flex justify-center mt-1">
                      {[1, 2, 3, 4, 5].map(star => (
                        <StarIcon
                          key={star}
                          className={`w-3 h-3 ${star <= Math.round(parseFloat(activeProductStats.avg)) ? 'text-amber-400 fill-current' : 'text-slate-800'}`}
                        />
                      ))}
                    </div>
                    <div className="text-[9px] text-slate-500 mt-1 font-semibold">{activeProductStats.total} đánh giá</div>
                  </div>
                  
                  <div className="flex-1 space-y-0.5">
                    {[5, 4, 3, 2, 1].map(star => {
                      const pct = activeProductStats.total > 0 ? Math.round((activeProductStats.breakdown[star] / activeProductStats.total) * 100) : 0;
                      return (
                        <div key={star} className="flex items-center gap-1.5 text-[9px] text-slate-400">
                          <span className="w-2 text-right">{star}</span>
                          <div className="flex-1 h-1 bg-slate-950 rounded-full overflow-hidden border border-slate-900">
                            <div 
                              className="h-full bg-amber-400 rounded-full" 
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="w-5 text-right text-[8px] text-slate-500">{activeProductStats.breakdown[star]}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : (
              /* All Products Header Card */
              <div className="bg-slate-950/40 border border-slate-800/80 rounded-2xl p-5 flex flex-col md:flex-row gap-5 items-start md:items-center">
                <div className="flex-1 min-w-0">
                  <span className="text-[9px] uppercase tracking-wider font-bold text-sky-400 bg-sky-500/10 border border-sky-500/20 px-2 py-0.5 rounded">
                    Tổng quan đánh giá
                  </span>
                  <h3 className="text-base font-bold text-white mt-1">Tất cả sản phẩm</h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Hiển thị phản hồi của khách hàng trên toàn bộ danh mục sản phẩm của cửa hàng.
                  </p>
                  <div className="flex items-center gap-3 mt-2 flex-wrap text-xs text-slate-350">
                    <div>
                      Có đánh giá: <span className="text-indigo-400 font-bold">{Object.keys(stats.counts).length}</span> / {products.length} sản phẩm
                    </div>
                  </div>
                </div>
                
                {/* Stats block */}
                <div className="w-full md:w-56 bg-slate-900/40 p-3 rounded-xl border border-slate-800/80 flex gap-3 items-center shrink-0">
                  <div className="text-center shrink-0 w-16">
                    <div className="text-2xl font-extrabold text-white leading-none">{activeProductStats.avg}</div>
                    <div className="flex justify-center mt-1">
                      {[1, 2, 3, 4, 5].map(star => (
                        <StarIcon
                          key={star}
                          className={`w-3 h-3 ${star <= Math.round(parseFloat(activeProductStats.avg)) ? 'text-amber-400 fill-current' : 'text-slate-800'}`}
                        />
                      ))}
                    </div>
                    <div className="text-[9px] text-slate-500 mt-1 font-semibold">{activeProductStats.total} đánh giá</div>
                  </div>
                  
                  <div className="flex-1 space-y-0.5">
                    {[5, 4, 3, 2, 1].map(star => {
                      const pct = activeProductStats.total > 0 ? Math.round((activeProductStats.breakdown[star] / activeProductStats.total) * 100) : 0;
                      return (
                        <div key={star} className="flex items-center gap-1.5 text-[9px] text-slate-400">
                          <span className="w-2 text-right">{star}</span>
                          <div className="flex-1 h-1 bg-slate-950 rounded-full overflow-hidden border border-slate-900">
                            <div 
                              className="h-full bg-amber-400 rounded-full" 
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="w-5 text-right text-[8px] text-slate-500">{activeProductStats.breakdown[star]}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* Filters Toolbar */}
            <div className="bg-slate-950/40 p-4 rounded-xl border border-slate-800/80 flex flex-wrap gap-4 items-center justify-between">
              
              {/* Left filter options */}
              <div className="flex flex-wrap gap-4 items-center flex-1">
                {/* Search in Reviews */}
                <div className="flex flex-col gap-1 w-full sm:max-w-xs">
                  <label className="text-[10px] uppercase font-bold text-slate-500">Tìm kiếm đánh giá</label>
                  <input
                    type="text"
                    value={reviewSearchQuery}
                    onChange={(e) => setReviewSearchQuery(e.target.value)}
                    placeholder="Nội dung, Đơn hàng, ID khách..."
                    className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-205 focus:outline-none focus:border-indigo-500 w-full placeholder:text-slate-650"
                  />
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-[10px] uppercase font-bold text-slate-500">Đánh giá sao</label>
                  <select
                    value={ratingFilter}
                    onChange={(e) => setRatingFilter(e.target.value)}
                    className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-202 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">Tất cả sao</option>
                    <option value="5">5 sao</option>
                    <option value="4">4 sao</option>
                    <option value="3">3 sao</option>
                    <option value="2">2 sao</option>
                    <option value="1">1 sao</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-[10px] uppercase font-bold text-slate-500">Trạng thái hiển thị</label>
                  <select
                    value={visibilityFilter}
                    onChange={(e) => setVisibilityFilter(e.target.value)}
                    className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-202 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">Tất cả trạng thái</option>
                    <option value="true">Hiển thị</option>
                    <option value="false">Đang ẩn</option>
                  </select>
                </div>
              </div>

              {/* Counter details */}
              <div className="text-xs text-slate-400 bg-slate-900/30 px-3 py-1.5 rounded-lg border border-slate-800/60 font-semibold shrink-0">
                Tìm thấy {filteredReviews.length} kết quả
              </div>
            </div>

            {/* Reviews Grid */}
            {filteredReviews.length === 0 ? (
              <div className="text-center py-16 bg-slate-950/20 rounded-xl border border-dashed border-slate-800">
                <p className="text-slate-500 text-sm">Không tìm thấy đánh giá nào khớp với bộ lọc</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {filteredReviews.map((rev) => (
                  <div
                    key={rev.id}
                    className={`p-5 rounded-2xl border transition-all ${
                      rev.is_visible 
                        ? 'bg-slate-950/30 border-slate-800/80 hover:border-slate-700/80 shadow-sm' 
                        : 'bg-slate-950/10 border-slate-900/60 opacity-60'
                    }`}
                  >
                    {/* Header inside Card */}
                    <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[11px] font-bold text-slate-400">
                            Đơn hàng: #{rev.order_id ? String(rev.order_id).slice(0, 8) : 'Không rõ'}
                          </span>
                          <span className="text-slate-750 text-xs">|</span>
                          <span className="text-[11px] font-semibold text-indigo-400">
                            Khách: u-{String(rev.user_id).slice(0, 6)}
                          </span>
                          {rev.is_verified && (
                            <span className="text-[9px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded font-bold">
                              Đã mua hàng
                            </span>
                          )}
                          {!rev.is_visible && (
                            <span className="text-[9px] text-amber-500 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded font-bold">
                              Đang ẩn
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-slate-500 font-medium">
                          Thời gian: {new Date(rev.created_at).toLocaleString('vi-VN')}
                        </p>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleToggleVisibility(rev.id, rev.is_visible)}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors border ${
                            rev.is_visible
                              ? 'bg-amber-950/10 hover:bg-amber-950/20 text-amber-400 border-amber-900/50'
                              : 'bg-emerald-950/10 hover:bg-emerald-950/20 text-emerald-400 border-emerald-900/50'
                          }`}
                        >
                          {rev.is_visible ? (
                            <>
                              <EyeSlashIcon className="w-3.5 h-3.5" />
                              Ẩn đánh giá
                            </>
                          ) : (
                            <>
                              <EyeIcon className="w-3.5 h-3.5" />
                              Hiển thị
                            </>
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Product badge inside review if viewing All Products */}
                    {!productFilter && (
                      <div className="flex items-center gap-3 p-2 bg-slate-900/40 rounded-xl border border-slate-800/60 mb-4">
                        <img
                          src={productsMap[rev.product_id]?.primary_image?.image || productsMap[rev.product_id]?.image || '/placeholder.png'}
                          alt={productsMap[rev.product_id]?.name || 'Sản phẩm'}
                          className="w-10 h-10 object-cover rounded-lg border border-slate-800 shrink-0 bg-slate-900"
                        />
                        <div className="min-w-0 flex-1">
                          <p className="text-[9px] uppercase tracking-wider font-bold text-slate-500">Sản phẩm đánh giá</p>
                          <Link
                            to={`/products/${rev.product_id}`}
                            target="_blank"
                            className="text-xs font-bold text-indigo-400 hover:text-indigo-350 hover:underline truncate block"
                          >
                            {productsMap[rev.product_id]?.name || `Mã sản phẩm: ${String(rev.product_id).slice(0, 8)}...`}
                          </Link>
                        </div>
                      </div>
                    )}

                    {/* Review Stars & Content */}
                    <div className="space-y-2 mb-4 bg-slate-900/20 p-3 rounded-xl border border-slate-900/50">
                      <div className="flex items-center gap-0.5">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <StarIcon
                            key={star}
                            className={`w-4 h-4 ${star <= rev.rating ? 'text-amber-400 fill-current' : 'text-slate-800'}`}
                          />
                        ))}
                      </div>
                      {rev.title && <h4 className="text-sm font-bold text-white leading-snug">{rev.title}</h4>}
                      <p className="text-slate-350 text-xs leading-relaxed whitespace-pre-line">{rev.content}</p>
                    </div>

                    {/* Replies Container */}
                    <div className="border-t border-slate-900/60 pt-4 space-y-4">
                      {rev.replies && rev.replies.length > 0 && (
                        <div className="space-y-3 bg-slate-900/30 p-3 rounded-xl border border-slate-900/40">
                          {rev.replies.map((reply) => (
                            <div key={reply.id} className="text-[11px]">
                              <div className="flex items-center gap-1.5 flex-wrap">
                                <span className="font-bold text-slate-200">
                                  {reply.is_seller ? 'Phản hồi từ người bán' : 'Khách hàng'}
                                </span>
                                {reply.is_seller && (
                                  <span className="bg-sky-500/10 text-sky-400 border border-sky-500/20 text-[8px] px-1.5 py-0.2 rounded-full font-bold">
                                    QTV
                                  </span>
                                )}
                                <span className="text-[10px] text-slate-500">
                                  {new Date(reply.created_at).toLocaleString('vi-VN')}
                                </span>
                              </div>
                              <p className="text-slate-400 mt-1 leading-relaxed whitespace-pre-line">{reply.content}</p>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Reply Form */}
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={replyTexts[rev.id] || ''}
                          onChange={(e) => handleReplyChange(rev.id, e.target.value)}
                          placeholder="Nhập phản hồi từ người bán..."
                          className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 placeholder:text-slate-650"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSubmitReply(rev.id);
                          }}
                        />
                        <button
                          onClick={() => handleSubmitReply(rev.id)}
                          disabled={submittingReply[rev.id] || !(replyTexts[rev.id] || '').trim()}
                          className="flex items-center gap-1.5 px-4 py-1.5 bg-indigo-650 hover:bg-indigo-600 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition-colors shrink-0"
                        >
                          <ChatBubbleLeftRightIcon className="w-3.5 h-3.5" />
                          {submittingReply[rev.id] ? 'Đang gửi...' : 'Phản hồi'}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
        </div>
      )}
    </div>
  );
};

export default AdminReviewsPage;
