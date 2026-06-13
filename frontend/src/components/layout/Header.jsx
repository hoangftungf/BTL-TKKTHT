import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import { logout } from '../../store/slices/authSlice';
import { fetchCategories } from '../../store/slices/productSlice';
import { setLoginModalOpen, toggleCartDrawer } from '../../store/slices/uiSlice';
import productService from '../../services/productService';
import NotificationDropdown from '../notification/NotificationDropdown';
import {
  Search,
  ShoppingBag,
  User,
  Menu,
  X,
  MapPin,
  ShieldCheck,
  Truck,
  RotateCcw,
  Calendar,
  Zap,
  BadgePercent,
  Home
} from 'lucide-react';
import { fadeInDown, staggerContainer, staggerItem, badgeBounce, popIn } from '../../utils/animations';

const Header = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const { isAuthenticated, user } = useSelector((state) => state.auth);
  const { totalItems } = useSelector((state) => state.cart);
  const { categories } = useSelector((state) => state.product);

  useEffect(() => {
    dispatch(fetchCategories());
  }, [dispatch]);

  // Track scroll for sticky header collapse
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Debounced search suggestions fetching
  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    setLoadingSuggestions(true);
    const timer = setTimeout(async () => {
      try {
        const data = await productService.suggestProducts(searchQuery);
        setSuggestions(data);
        setShowSuggestions(true);
      } catch (err) {
        console.error('Fetch search suggestions error:', err);
      } finally {
        setLoadingSuggestions(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Handle click outside to close suggestions
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (!e.target.closest('.search-container')) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('click', handleOutsideClick);
    return () => document.removeEventListener('click', handleOutsideClick);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setShowSuggestions(false);
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleLogout = () => {
    dispatch(logout());
    navigate('/');
  };

  // Helper keyword click
  const handleKeywordClick = (keyword) => {
    setSearchQuery(keyword);
    navigate(`/search?q=${encodeURIComponent(keyword)}`);
  };

  const hotKeywords = ['điện gia dụng', 'xe cộ', 'mẹ & bé', 'khỏe đẹp', 'nhà cửa', 'sách', 'thể thao'];

  return (
    <motion.header
      className="backdrop-blur-glass sticky top-0 z-50 w-full border-b border-slate-100 shadow-custom-smooth"
      animate={{
        boxShadow: isScrolled ? '0 4px 20px rgba(0,0,0,0.08)' : '0 1px 2px rgba(0,0,0,0.04)',
      }}
      transition={{ duration: 0.3 }}
    >
      {/* 1. Dark Promo Ribbon */}
      <motion.div
        className="bg-slate-900 text-slate-200 py-2 text-center text-xs font-medium select-none flex items-center justify-center gap-1.5 border-b border-slate-800"
        animate={{ height: isScrolled ? 0 : 'auto', opacity: isScrolled ? 0 : 1, paddingTop: isScrolled ? 0 : 8, paddingBottom: isScrolled ? 0 : 8 }}
        transition={{ duration: 0.3 }}
      >
        <Truck className="w-4 h-4 text-sky-400 animate-bounce" />
        <span>Freeship đơn từ 45k, giảm nhiều hơn cùng <strong className="text-sky-400">FREESHIP XTRA</strong></span>
      </motion.div>

      {/* 2. Main Navigation Bar */}
      <motion.div
        className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8"
        animate={{ paddingTop: isScrolled ? 8 : 12, paddingBottom: isScrolled ? 8 : 12 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center justify-between gap-4 md:gap-8">
          {/* Logo */}
          <Link to="/" className="flex flex-col items-start leading-tight shrink-0">
            <span className="text-2xl font-black text-slate-900 tracking-tight flex items-center font-display">
              TIKI<span className="text-sky-400 text-xs font-bold ml-1 bg-sky-50 px-1 rounded">AI</span>
            </span>
            <span className="text-[10px] text-slate-500 font-semibold tracking-wide">Tốt & Nhanh</span>
          </Link>

          {/* Search container */}
          <div className="hidden md:flex flex-col search-container relative z-40">
            <motion.form
              onSubmit={handleSearch}
              className="flex items-center bg-slate-100 rounded-full px-4 py-2 text-sm border border-transparent"
              animate={{
                width: searchQuery ? '32rem' : '24rem',
                backgroundColor: searchQuery ? 'rgb(255 255 255)' : 'rgb(241 245 249)',
                borderColor: searchQuery ? 'rgb(226 232 240)' : 'transparent',
                boxShadow: searchQuery ? '0 4px 12px rgba(0,0,0,0.08)' : 'none',
              }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
            >
              <input
                type="text"
                value={searchQuery}
                onFocus={() => {
                  if (suggestions.length > 0) setShowSuggestions(true);
                }}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm sản phẩm, thương hiệu..."
                className="flex-1 bg-transparent focus:outline-none text-slate-800 placeholder-slate-400"
              />

              {loadingSuggestions ? (
                <div className="mr-1">
                  <svg className="animate-spin h-4 w-4 text-slate-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              ) : (
                <motion.button
                  type="submit"
                  className="text-slate-500 hover:text-slate-800 transition-colors"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <Search className="w-4 h-4" />
                </motion.button>
              )}
            </motion.form>

            {/* Suggestions list popup */}
            <AnimatePresence>
              {showSuggestions && suggestions.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: -8, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.98 }}
                  transition={{ duration: 0.2 }}
                  className="absolute left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto divide-y divide-gray-100"
                >
                  <AnimatePresence>
                    {suggestions.map((item) => (
                      <motion.button
                        key={item.id}
                        type="button"
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        transition={{ duration: 0.15 }}
                        onClick={() => {
                          setSearchQuery('');
                          setShowSuggestions(false);
                          navigate(`/products/${item.id}`);
                        }}
                        className="w-full flex items-center px-4 py-3 hover:bg-gray-50 text-left transition-colors"
                      >
                        {item.image ? (
                          <img
                            src={item.image}
                            alt={item.name}
                            className="w-10 h-10 object-cover rounded mr-3 flex-shrink-0"
                          />
                        ) : (
                          <div className="w-10 h-10 bg-gray-100 rounded mr-3 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">{item.name}</p>
                          <div className="flex items-center space-x-2 mt-0.5">
                            <span className="text-xs text-red-600 font-semibold">
                              {item.price ? item.price.toLocaleString('vi-VN') + ' đ' : ''}
                            </span>
                            {item.category_name && (
                              <span className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                                {item.category_name}
                              </span>
                            )}
                          </div>
                        </div>
                      </motion.button>
                    ))}
                  </AnimatePresence>
                  <button
                    type="button"
                    onClick={() => {
                      setShowSuggestions(false);
                      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
                    }}
                    className="w-full text-center py-2.5 text-xs text-blue-600 font-medium hover:bg-gray-50 block transition-colors border-t border-gray-100"
                  >
                    Xem tất cả kết quả cho "{searchQuery}"
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Hot keyword suggestions & Delivery Address row */}
            <div className="flex items-center justify-between mt-1 text-[11px] text-gray-500">
              <div className="flex items-center gap-2 overflow-x-auto whitespace-nowrap scrollbar-none">
                {hotKeywords.map((kw, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleKeywordClick(kw)}
                    className="hover:text-blue-600 transition-colors"
                  >
                    {kw}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-1 cursor-pointer hover:text-blue-600 shrink-0 ml-4 select-none">
                <MapPin className="w-3 h-3 text-gray-400" />
                <span>Giao đến: </span>
                <span className="font-semibold text-gray-700 underline truncate max-w-[150px]">Q. Hoàn Kiếm, Hà Nội</span>
              </div>
            </div>
          </div>

          {/* Right menu actions */}
          <div className="flex items-center gap-2 md:gap-4 shrink-0">
            {/* Trang chủ link */}
            <Link to="/" className="hidden lg:flex items-center gap-1.5 text-slate-600 hover:text-sky-400 py-1.5 px-2.5 rounded-lg hover:bg-slate-50 transition-all font-medium text-sm">
              <Home className="w-5 h-5 text-slate-500 hover:text-sky-400" />
              <span>Trang chủ</span>
            </Link>

            {/* User Profile / Login */}
            {isAuthenticated ? (
              <div className="relative group">
                <motion.button
                  className="flex items-center gap-1.5 text-slate-600 hover:text-sky-400 py-1.5 px-2.5 rounded-lg hover:bg-slate-50 transition-all font-medium text-sm"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <User className="w-5 h-5 text-slate-500" />
                  <span className="hidden sm:block truncate max-w-[100px]">{user?.email?.split('@')[0]}</span>
                </motion.button>
                <AnimatePresence>
                  <motion.div
                    initial={{ opacity: 0, y: -4, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -4, scale: 0.96 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-slate-100 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 py-1"
                  >
                    <Link to="/profile" className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50">
                      Tài khoản của tôi
                    </Link>
                    <Link to="/orders" className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50">
                      Lịch sử đơn hàng
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-50 border-t border-gray-50"
                    >
                      Đăng xuất
                    </button>
                  </motion.div>
                </AnimatePresence>
              </div>
            ) : (
              <motion.button
                onClick={() => dispatch(setLoginModalOpen(true))}
                className="flex items-center gap-1.5 text-slate-600 hover:text-sky-400 py-1.5 px-2.5 rounded-lg hover:bg-slate-50 transition-all font-medium text-sm"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <User className="w-5 h-5 text-slate-500" />
                <span className="hidden sm:block">Đăng nhập</span>
              </motion.button>
            )}

            {/* Notifications Dropdown */}
            {isAuthenticated && (
              <NotificationDropdown theme="light" />
            )}

            {/* Shopping Cart */}
            <motion.button
              onClick={() => dispatch(toggleCartDrawer())}
              className="relative p-2 text-slate-600 hover:text-sky-400 hover:bg-slate-50 rounded-lg transition-all flex items-center gap-1.5 cart-icon-trigger"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <div className="relative">
                <ShoppingBag className="w-6 h-6 text-slate-600" />
                <AnimatePresence>
                  {totalItems > 0 && (
                    <motion.span
                      key={totalItems}
                      variants={badgeBounce}
                      initial="initial"
                      animate="animate"
                      exit={{ scale: 0 }}
                      className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center"
                    >
                      {totalItems > 99 ? '99+' : totalItems}
                    </motion.span>
                  )}
                </AnimatePresence>
              </div>
            </motion.button>

            {/* Mobile Menu Toggle */}
            <motion.button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 text-gray-600 hover:bg-gray-50 rounded-lg"
              whileTap={{ scale: 0.9 }}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </motion.button>
          </div>
        </div>

        {/* Mobile Search */}
        <div className="md:hidden mt-2 search-container relative">
          <form onSubmit={handleSearch} className="flex">
            <div className="relative flex-1">
              <input
                type="text"
                value={searchQuery}
                onFocus={() => {
                  if (suggestions.length > 0) setShowSuggestions(true);
                }}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm sản phẩm..."
                className="w-full pl-9 pr-4 py-1.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-sky-400 text-sm"
              />
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />

              {loadingSuggestions && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <svg className="animate-spin h-4 w-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
              )}
            </div>
          </form>

          {/* Mobile Search suggestions */}
          <AnimatePresence>
            {showSuggestions && suggestions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className="absolute left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto divide-y divide-gray-100"
              >
                {suggestions.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      setSearchQuery('');
                      setShowSuggestions(false);
                      navigate(`/products/${item.id}`);
                    }}
                    className="w-full flex items-center px-3 py-2 hover:bg-gray-50 text-left transition-colors"
                  >
                    {item.image ? (
                      <img
                        src={item.image}
                        alt={item.name}
                        className="w-8 h-8 object-cover rounded mr-2 flex-shrink-0"
                      />
                    ) : (
                      <div className="w-8 h-8 bg-gray-100 rounded mr-2 flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-gray-900 truncate">{item.name}</p>
                      <span className="text-[10px] text-red-600 font-semibold">
                        {item.price ? item.price.toLocaleString('vi-VN') + ' đ' : ''}
                      </span>
                    </div>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>

      {/* 3. Commitments/Benefits Bar */}
      <motion.div
        className="bg-white border-t border-gray-100 hidden md:block text-xs text-gray-500"
        animate={{
          height: isScrolled ? 0 : 'auto',
          opacity: isScrolled ? 0 : 1,
          paddingTop: isScrolled ? 0 : 8,
          paddingBottom: isScrolled ? 0 : 8,
          overflow: 'hidden',
        }}
        transition={{ duration: 0.25 }}
      >
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 flex items-center gap-6 justify-start font-medium select-none">
          <span className="text-gray-400">Cam kết:</span>
          <span className="flex items-center gap-1"><ShieldCheck className="w-3.5 h-3.5 text-slate-800" /> 100% hàng thật</span>
          <span className="flex items-center gap-1"><Truck className="w-3.5 h-3.5 text-slate-800" /> Freeship mọi đơn</span>
          <span className="flex items-center gap-1"><RotateCcw className="w-3.5 h-3.5 text-slate-800" /> Hoàn tiền 200%</span>
          <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5 text-slate-800" /> 30 ngày đổi trả</span>
          <span className="flex items-center gap-1"><Zap className="w-3.5 h-3.5 text-slate-800" /> Giao nhanh 2h</span>
          <span className="flex items-center gap-1"><BadgePercent className="w-3.5 h-3.5 text-slate-800" /> Giá siêu rẻ</span>
        </div>
      </motion.div>

      {/* Mobile Drawer Navigation Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="md:hidden border-t border-gray-100 bg-white px-4 overflow-hidden"
          >
            <motion.nav
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
              className="flex flex-col py-3 space-y-1 text-sm font-medium"
            >
              <motion.div variants={staggerItem}>
                <Link
                  to="/"
                  onClick={() => setMobileMenuOpen(false)}
                  className="py-2.5 hover:text-sky-400 border-b border-gray-50 flex items-center gap-2"
                >
                  <Home className="w-4 h-4 text-gray-500" />
                  <span>Trang chủ</span>
                </Link>
              </motion.div>
              <motion.div variants={staggerItem}>
                <Link
                  to="/products"
                  onClick={() => setMobileMenuOpen(false)}
                  className="py-2.5 hover:text-sky-400 border-b border-gray-50 flex items-center gap-2"
                >
                  <BadgePercent className="w-4 h-4 text-gray-500" />
                  <span>Tất cả sản phẩm</span>
                </Link>
              </motion.div>
              {categories && categories.slice(0, 5).map((category) => (
                <motion.div key={category.id} variants={staggerItem}>
                  <Link
                    to={`/products?category=${category.id}`}
                    onClick={() => setMobileMenuOpen(false)}
                    className="py-2 pl-6 hover:text-sky-400 text-gray-600 border-b border-gray-50 flex items-center gap-2 text-xs"
                  >
                    <span>• {category.name}</span>
                  </Link>
                </motion.div>
              ))}
            </motion.nav>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
};

export default Header;
