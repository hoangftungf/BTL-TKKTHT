import React from 'react';
import { Carousel } from 'antd';
import { 
  Truck, 
  Ticket, 
  Globe, 
  Flame, 
  Store, 
  TrendingUp, 
  BadgePercent, 
  ShieldCheck,
  Gamepad2,
  Award
} from 'lucide-react';
import { Link } from 'react-router-dom';

const HeroSection = () => {
  const banners = [
    {
      id: 1,
      image: '/tech_banner.png',
      title: 'Đại tiệc Công nghệ',
      link: '/products'
    },
    {
      id: 2,
      image: '/fashion_banner.png',
      title: 'Fashion Summer Sale',
      link: '/products'
    }
  ];

  const quickLinks = [
    {
      id: 1,
      label: 'Freeship Xtra',
      icon: <Truck className="w-5 h-5 text-green-600" />,
      bgColor: 'bg-green-50 hover:bg-green-100',
      link: '/products'
    },
    {
      id: 2,
      label: 'Mã Giảm Giá',
      icon: <Ticket className="w-5 h-5 text-blue-600" />,
      bgColor: 'bg-blue-50 hover:bg-blue-100',
      link: '/products'
    },
    {
      id: 3,
      label: 'Hàng Quốc Tế',
      icon: <Globe className="w-5 h-5 text-indigo-600" />,
      bgColor: 'bg-indigo-50 hover:bg-indigo-100',
      link: '/products'
    },
    {
      id: 4,
      label: 'Deal Siêu Hot',
      icon: <Flame className="w-5 h-5 text-red-600" />,
      bgColor: 'bg-red-50 hover:bg-red-100',
      link: '/products?is_featured=true'
    },
    {
      id: 5,
      label: 'Tiki Trading',
      icon: <Store className="w-5 h-5 text-purple-600" />,
      bgColor: 'bg-purple-50 hover:bg-purple-100',
      link: '/products'
    },
    {
      id: 6,
      label: 'Xu Hướng',
      icon: <TrendingUp className="w-5 h-5 text-orange-600" />,
      bgColor: 'bg-orange-50 hover:bg-orange-100',
      link: '/products'
    },
    {
      id: 7,
      label: 'Giá Siêu Rẻ',
      icon: <BadgePercent className="w-5 h-5 text-yellow-600" />,
      bgColor: 'bg-yellow-50 hover:bg-yellow-100',
      link: '/products'
    },
    {
      id: 8,
      label: 'Hoàn Tiền 200%',
      icon: <ShieldCheck className="w-5 h-5 text-teal-600" />,
      bgColor: 'bg-teal-50 hover:bg-teal-100',
      link: '/products'
    },
    {
      id: 9,
      label: 'Tiki Game',
      icon: <Gamepad2 className="w-5 h-5 text-pink-600" />,
      bgColor: 'bg-pink-50 hover:bg-pink-100',
      link: '/products'
    },
    {
      id: 10,
      label: 'Thương Hiệu',
      icon: <Award className="w-5 h-5 text-cyan-600" />,
      bgColor: 'bg-cyan-50 hover:bg-cyan-100',
      link: '/products'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Banner Carousel */}
      <div className="w-full rounded-xl overflow-hidden shadow-sm border border-gray-100">
        <Carousel autoplay effect="fade" dotPosition="bottom">
          {banners.map((banner) => (
            <div key={banner.id} className="relative aspect-[21/9] md:aspect-[24/8] w-full">
              <Link to={banner.link} className="block w-full h-full">
                <img
                  src={banner.image}
                  alt={banner.title}
                  className="w-full h-full object-cover"
                />
              </Link>
            </div>
          ))}
        </Carousel>
      </div>

      {/* Quick Links Grid */}
      <div className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
        <div className="grid grid-cols-5 md:grid-cols-10 gap-4">
          {quickLinks.map((item) => (
            <Link
              key={item.id}
              to={item.link}
              className="flex flex-col items-center group cursor-pointer"
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 shadow-sm ${item.bgColor} group-hover:scale-110 group-hover:shadow-md`}>
                {item.icon}
              </div>
              <span className="text-[11px] text-gray-700 font-medium text-center mt-2 group-hover:text-blue-600 transition-colors line-clamp-2 leading-tight max-w-[70px]">
                {item.label}
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default HeroSection;
