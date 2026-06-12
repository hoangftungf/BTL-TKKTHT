import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { searchService } from '../services/aiService';
import productService from '../services/productService';
import ProductGrid from '../components/product/ProductGrid';
import ProductRecommendations from '../components/product/ProductRecommendations';

const SearchPage = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [suggestions, setSuggestions] = useState([]);
  const [categories, setCategories] = useState([]);

  const { user, isAuthenticated } = useSelector((state) => state.auth);

  useEffect(() => {
    const searchWithAI = async () => {
      if (!query) return;

      setLoading(true);
      try {
        const response = await searchService.search(query);
        const results = response.data.results || [];

        // Map results to product format
        const mappedProducts = results.map((r) => ({
          id: r.product_id,
          name: r.name,
          price: r.price,
          category: r.category,
          brand: r.brand,
          ...r.product,
        }));

        setProducts(mappedProducts);
        setTotal(response.data.total || 0);
      } catch (error) {
        console.error('Search error:', error);
        setProducts([]);
      } finally {
        setLoading(false);
      }
    };

    searchWithAI();
  }, [query]);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (query.length >= 2) {
        try {
          const response = await searchService.autocomplete(query, 5);
          setSuggestions(response.data.suggestions || []);
        } catch (error) {
          setSuggestions([]);
        }
      }
    };

    fetchSuggestions();
  }, [query]);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const data = await productService.getCategories();
        // Lấy 6 danh mục đầu tiên làm danh mục nổi bật
        setCategories(data.slice(0, 6));
      } catch (error) {
        console.error('Error fetching categories:', error);
      }
    };
    fetchCategories();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        Kết quả tìm kiếm
      </h1>
      <p className="text-gray-500 mb-4">
        {total} kết quả cho "{query}"
      </p>

      {suggestions.length > 0 && (
        <div className="mb-6">
          <p className="text-sm text-gray-500 mb-2">Gợi ý tìm kiếm:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((s, index) => (
              <a
                key={index}
                href={`/search?q=${encodeURIComponent(s.text)}`}
                className="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-700 hover:bg-gray-200"
              >
                {s.text}
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Main search results or Zero-Result State */}
      {!loading && products.length === 0 ? (
        <div className="my-12 flex flex-col items-center justify-center text-center p-8 bg-gradient-to-b from-slate-50 to-white rounded-3xl border border-gray-100 shadow-sm max-w-3xl mx-auto">
          {/* SVG Illustration dễ thương cho Empty State */}
          <div className="w-40 h-40 mb-6 text-indigo-500 animate-bounce" style={{ animationDuration: '3s' }}>
            <svg viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
              <circle cx="100" cy="100" r="80" fill="url(#paint0_linear)" fillOpacity="0.1" />
              <path d="M140 140L120 120" stroke="currentColor" strokeWidth="6" strokeLinecap="round" />
              <circle cx="95" cy="95" r="35" stroke="currentColor" strokeWidth="6" />
              <circle cx="85" cy="85" r="4" fill="currentColor" />
              <circle cx="105" cy="85" r="4" fill="currentColor" />
              <path d="M90 108C92.5 104 97.5 104 100 108" stroke="currentColor" strokeWidth="4" strokeLinecap="round" />
              <defs>
                <linearGradient id="paint0_linear" x1="20" y1="20" x2="180" y2="180" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#6366F1" />
                  <stop offset="1" stopColor="#4F46E5" />
                </linearGradient>
              </defs>
            </svg>
          </div>

          <h2 className="text-xl font-bold text-gray-900 mb-2">
            Rất tiếc, không tìm thấy kết quả phù hợp cho "{query}"
          </h2>
          <p className="text-gray-500 max-w-md mb-6 text-sm">
            Chúng tôi đã tìm kiếm kỹ lưỡng nhưng chưa thấy sản phẩm nào phù hợp. Bạn hãy thử kiểm tra lại từ khóa hoặc tham khảo các gợi ý dưới đây nhé!
          </p>

          {/* Gợi ý sửa lỗi */}
          <div className="bg-slate-50 rounded-2xl p-5 text-left w-full mb-8 border border-slate-100/80">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Mẹo tìm kiếm:</h4>
            <ul className="text-xs text-slate-500 space-y-1.5 list-disc list-inside">
              <li>Kiểm tra lại xem từ khóa đã gõ đúng chính tả chưa.</li>
              <li>Thử các từ khóa chung chung hơn (ví dụ: gõ "giày" thay cho "giày sneaker thể thao nam cao cấp").</li>
              <li>Sử dụng các cụm từ đồng nghĩa phổ biến (ví dụ: "smartphone" thay vì "điện thoại").</li>
            </ul>
          </div>

          {/* Danh mục nổi bật */}
          {categories.length > 0 && (
            <div className="w-full">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 text-center">Khám phá các danh mục bán chạy</h4>
              <div className="flex flex-wrap justify-center gap-2">
                {categories.map((cat) => (
                  <a
                    key={cat.id}
                    href={`/products?category=${cat.id}`}
                    className="px-4 py-2 bg-white hover:bg-indigo-50 border border-gray-200 hover:border-indigo-300 rounded-xl text-xs font-semibold text-gray-700 hover:text-indigo-600 shadow-sm transition-all duration-200 hover:-translate-y-0.5"
                  >
                    {cat.name}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <ProductGrid
          products={products}
          loading={loading}
          emptyMessage={`Không tìm thấy sản phẩm cho "${query}"`}
        />
      )}

      {/* AI Recommendations - luôn render để níu kéo khách hàng */}
      <div className="mt-12 border-t border-gray-200">
        {/* Gợi ý cá nhân hóa nếu đăng nhập */}
        {isAuthenticated && user?.id && (
          <ProductRecommendations
            userId={user.id}
            type="personalized"
            title="Được gợi ý riêng cho bạn"
            limit={6}
          />
        )}

        {/* Sản phẩm xu hướng phổ biến */}
        <ProductRecommendations
          type="trending"
          title="Xu hướng mua sắm nổi bật"
          limit={6}
        />
      </div>
    </div>
  );
};

export default SearchPage;
