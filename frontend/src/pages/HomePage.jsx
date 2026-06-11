import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchFeaturedProducts, fetchCategories } from '../store/slices/productSlice';
import ProductGrid from '../components/product/ProductGrid';
import ProductRecommendations from '../components/product/ProductRecommendations';
import HeroSection from '../components/layout/HeroSection';
import { Menu } from 'antd';
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
  Box,
  ChevronRight
} from 'lucide-react';

const HomePage = () => {
  const dispatch = useDispatch();
  const { featuredProducts, categories } = useSelector((state) => state.product);
  const { user } = useSelector((state) => state.auth);

  useEffect(() => {
    dispatch(fetchFeaturedProducts());
    dispatch(fetchCategories());
  }, [dispatch]);

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

  const getSubcategories = (name) => {
    const n = name.toLowerCase();
    if (n.includes('thoại')) return ['Apple iPhone', 'Samsung Galaxy', 'Xiaomi', 'Oppo', 'Phụ kiện điện thoại'];
    if (n.includes('lap')) return ['MacBook Air', 'Asus Gaming', 'Dell Latitude', 'HP ProBook', 'Phụ kiện Laptop'];
    if (n.includes('trang')) return ['Thời trang nam', 'Thời trang nữ', 'Phụ kiện', 'Túi xách hot'];
    if (n.includes('sách')) return ['Sách Ngoại Ngữ', 'Sách Kỹ Năng', 'Sách Tiểu Thuyết', 'Sách Giáo Khoa'];
    if (n.includes('dụng')) return ['Bếp ga, bếp từ', 'Nồi chiên không dầu', 'Đồ dùng nhà bếp'];
    if (n.includes('mỹ')) return ['Kem chống nắng', 'Son môi chính hãng', 'Sữa rửa mặt', 'Nước tẩy trang'];
    return ['Sản phẩm bán chạy', 'Hàng mới về', 'Khuyến mãi hot'];
  };

  const menuItems = categories.map((category) => {
    const subs = getSubcategories(category.name);
    return {
      key: category.id,
      label: <span className="font-semibold text-gray-700 text-sm">{category.name}</span>,
      icon: getCategoryIcon(category.name),
      children: subs.map((sub, idx) => ({
        key: `${category.id}-sub-${idx}`,
        label: (
          <Link 
            to={`/products?category=${category.id}&q=${encodeURIComponent(sub)}`}
            className="text-xs text-gray-600 hover:text-blue-600 block w-full py-0.5"
          >
            {sub}
          </Link>
        )
      }))
    };
  });

  return (
    <div className="bg-gray-50 min-h-screen">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex gap-6 items-start">
          {/* Sidebar */}
          <aside className="hidden md:block w-1/5 shrink-0 bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <h2 className="text-base font-bold text-gray-900 mb-4 px-2 flex items-center gap-2">
              <span className="w-1 h-4 bg-blue-600 rounded-full"></span>
              Danh mục sản phẩm
            </h2>
            <Menu
              mode="inline"
              items={menuItems}
              className="border-none tiki-menu"
              style={{ background: 'transparent' }}
            />
          </aside>

          {/* Main Content */}
          <div className="w-full md:w-4/5 flex-grow space-y-6">
            {/* Hero Section */}
            <HeroSection />

            {/* Personalized Recommendations */}
            {user && (
              <ProductRecommendations
                type="personalized"
                userId={user.id}
                title="Gợi ý cho bạn"
                limit={6}
              />
            )}

            {/* Trending Products */}
            <ProductRecommendations
              type="trending"
              title="Sản phẩm bán chạy"
              limit={6}
            />

            {/* Featured Products */}
            <section className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <span className="w-1.5 h-5 bg-blue-600 rounded-full"></span>
                  Sản phẩm nổi bật
                </h2>
                <Link to="/products?is_featured=true" className="text-sm font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1">
                  Xem tất cả <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
              <ProductGrid products={featuredProducts} loading={featuredProducts.length === 0} />
            </section>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
