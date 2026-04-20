import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchFeaturedProducts, fetchCategories } from '../store/slices/productSlice';
import { recommendationService } from '../services/aiService';
import ProductGrid from '../components/product/ProductGrid';
import { ArrowRightIcon, SparklesIcon, TruckIcon, ShieldCheckIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';

const HomePage = () => {
  const dispatch = useDispatch();
  const { featuredProducts, categories, loading } = useSelector((state) => state.product);
  const { user } = useSelector((state) => state.auth);

  const [trending, setTrending] = useState([]);
  const [personalized, setPersonalized] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    dispatch(fetchFeaturedProducts());
    dispatch(fetchCategories());
  }, [dispatch]);

  useEffect(() => {
    const fetchRecommendations = async () => {
      setAiLoading(true);
      try {
        // Fetch trending
        const trendingRes = await recommendationService.getTrending(8);
        setTrending(trendingRes.data.products || []);

        // Fetch personalized if logged in
        if (user?.id) {
          const personalizedRes = await recommendationService.getPersonalized(user.id, 8);
          setPersonalized(personalizedRes.data.products || []);
        }
      } catch (error) {
        console.error('Recommendation fetch error:', error);
      } finally {
        setAiLoading(false);
      }
    };

    fetchRecommendations();
  }, [user]);

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-primary-600 to-primary-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                Mua sắm thông minh với <span className="text-yellow-300">AI</span>
              </h1>
              <p className="text-lg text-primary-100 mb-8">
                Trải nghiệm mua sắm hiện đại với gợi ý cá nhân hóa, tìm kiếm thông minh và chatbot hỗ trợ 24/7.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link to="/products" className="btn bg-white text-primary-600 hover:bg-gray-100">
                  Khám phá ngay
                  <ArrowRightIcon className="w-5 h-5 ml-2" />
                </Link>
                <Link to="/ai-chat" className="btn border-2 border-white text-white hover:bg-white/10">
                  <SparklesIcon className="w-5 h-5 mr-2" />
                  Chat với AI
                </Link>
              </div>
            </div>
            <div className="hidden md:block">
              <img
                src="https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=600"
                alt="Shopping"
                className="rounded-2xl shadow-2xl"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center p-6">
              <TruckIcon className="w-10 h-10 text-primary-600 mx-auto mb-3" />
              <h3 className="font-semibold">Giao hàng nhanh</h3>
              <p className="text-sm text-gray-500">Giao hàng toàn quốc</p>
            </div>
            <div className="text-center p-6">
              <ShieldCheckIcon className="w-10 h-10 text-primary-600 mx-auto mb-3" />
              <h3 className="font-semibold">Bảo hành chính hãng</h3>
              <p className="text-sm text-gray-500">Cam kết 100% chính hãng</p>
            </div>
            <div className="text-center p-6">
              <ChatBubbleLeftRightIcon className="w-10 h-10 text-primary-600 mx-auto mb-3" />
              <h3 className="font-semibold">Hỗ trợ 24/7</h3>
              <p className="text-sm text-gray-500">Chatbot AI hỗ trợ</p>
            </div>
            <div className="text-center p-6">
              <SparklesIcon className="w-10 h-10 text-primary-600 mx-auto mb-3" />
              <h3 className="font-semibold">Gợi ý thông minh</h3>
              <p className="text-sm text-gray-500">AI cá nhân hóa</p>
            </div>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Danh mục sản phẩm</h2>
            <Link to="/products" className="text-primary-600 hover:underline flex items-center">
              Xem tất cả <ArrowRightIcon className="w-4 h-4 ml-1" />
            </Link>
          </div>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-4">
            {categories.slice(0, 6).map((category) => (
              <Link
                key={category.id}
                to={`/products?category=${category.id}`}
                className="card p-4 text-center hover:shadow-md transition-shadow"
              >
                <div className="w-16 h-16 bg-primary-100 rounded-full mx-auto mb-3 flex items-center justify-center">
                  <span className="text-2xl">📦</span>
                </div>
                <h3 className="font-medium text-sm text-gray-900 line-clamp-2">{category.name}</h3>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Personalized Recommendations */}
      {user && personalized.length > 0 && (
        <section className="py-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold text-gray-900">
                <SparklesIcon className="w-6 h-6 inline mr-2 text-yellow-500" />
                Gợi ý cho bạn
              </h2>
            </div>
            <ProductGrid products={personalized} loading={aiLoading} />
          </div>
        </section>
      )}

      {/* Trending Products */}
      {trending.length > 0 && (
        <section className="py-12 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold text-gray-900">Xu hướng</h2>
            </div>
            <ProductGrid products={trending} loading={aiLoading} />
          </div>
        </section>
      )}

      {/* Featured Products */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Sản phẩm nổi bật</h2>
            <Link to="/products?is_featured=true" className="text-primary-600 hover:underline flex items-center">
              Xem tất cả <ArrowRightIcon className="w-4 h-4 ml-1" />
            </Link>
          </div>
          <ProductGrid products={featuredProducts} loading={loading} />
        </div>
      </section>

      {/* CTA Banner */}
      <section className="py-12 bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Đăng ký nhận ưu đãi</h2>
          <p className="text-gray-400 mb-6 max-w-xl mx-auto">
            Nhận ngay mã giảm giá 10% cho đơn hàng đầu tiên khi đăng ký nhận tin từ chúng tôi.
          </p>
          <form className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
            <input
              type="email"
              placeholder="Email của bạn"
              className="flex-grow px-4 py-3 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <button type="submit" className="btn-primary px-6">
              Đăng ký
            </button>
          </form>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
