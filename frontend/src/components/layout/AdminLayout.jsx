import { useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { logout } from '../../store/slices/authSlice';
import {
  HomeIcon,
  ShoppingBagIcon,
  ClipboardDocumentListIcon,
  UsersIcon,
  CpuChipIcon,
  ArrowLeftIcon,
  Bars3Icon,
  XMarkIcon,
  BellIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/react/24/outline';

const AdminLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);

  const menuItems = [
    { name: 'Tổng quan', path: '/admin-dashboard', icon: HomeIcon },
    { name: 'Sản phẩm', path: '/admin-dashboard/products', icon: ShoppingBagIcon },
    { name: 'Đơn hàng', path: '/admin-dashboard/orders', icon: ClipboardDocumentListIcon },
    { name: 'Thành viên', path: '/admin-dashboard/users', icon: UsersIcon },
    { name: 'Giám sát AI', path: '/admin-dashboard/ai', icon: CpuChipIcon },
  ];

  const handleLogout = () => {
    dispatch(logout());
    navigate('/');
  };

  const isActive = (path) => {
    if (path === '/admin-dashboard') {
      return location.pathname === '/admin-dashboard';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex font-sans">
      {/* Mobile Sidebar Backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden transition-opacity duration-300"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Component */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-slate-950 border-r border-slate-800/80 flex flex-col justify-between
        transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:h-screen
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Sidebar Header */}
        <div>
          <div className="h-16 flex items-center justify-between px-6 border-b border-slate-800/80">
            <Link to="/admin-dashboard" className="flex items-center space-x-2.5">
              <div className="w-9 h-9 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-600/30">
                <span className="text-white font-extrabold text-lg">AI</span>
              </div>
              <div>
                <span className="text-base font-bold text-white tracking-wider block">ADMIN PANEL</span>
                <span className="text-[10px] text-slate-500 font-semibold block -mt-1">E-Commerce System</span>
              </div>
            </Link>
            <button 
              className="lg:hidden p-1 rounded-md text-slate-400 hover:text-white focus:outline-none"
              onClick={() => setSidebarOpen(false)}
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Sidebar Menu Items */}
          <nav className="mt-6 px-4 space-y-1.5">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200
                    ${active 
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20' 
                      : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'}
                  `}
                >
                  <Icon className={`w-5 h-5 flex-shrink-0 ${active ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-slate-800/80">
          <div className="flex items-center space-x-3 p-2 rounded-lg bg-slate-900/60 mb-3">
            <div className="w-9 h-9 bg-slate-800 rounded-full flex items-center justify-center font-bold text-indigo-400 border border-slate-700">
              {user?.username?.substring(0, 2).toUpperCase() || 'AD'}
            </div>
            <div className="flex-grow min-w-0">
              <p className="text-xs font-semibold text-white truncate">{user?.username || 'Administrator'}</p>
              <p className="text-[10px] text-slate-500 capitalize truncate font-medium">{user?.role || 'Admin'}</p>
            </div>
          </div>

          <Link
            to="/"
            className="flex items-center space-x-3 px-4 py-2.5 rounded-lg text-xs font-medium text-slate-400 hover:bg-slate-900 hover:text-slate-200 transition-colors"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            <span>Về trang chủ</span>
          </Link>

          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 px-4 py-2.5 mt-1 rounded-lg text-xs font-medium text-rose-400 hover:bg-rose-950/25 hover:text-rose-300 transition-colors focus:outline-none"
          >
            <ArrowRightOnRectangleIcon className="w-4 h-4" />
            <span>Đăng xuất</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto h-screen">
        {/* Top Header */}
        <header className="h-16 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/50 sticky top-0 z-30 flex items-center justify-between px-6">
          <div className="flex items-center space-x-4">
            <button
              className="lg:hidden p-1 rounded-md text-slate-400 hover:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              onClick={() => setSidebarOpen(true)}
            >
              <Bars3Icon className="w-6 h-6" />
            </button>
            <h1 className="text-lg font-bold text-white tracking-wide">
              {menuItems.find(item => isActive(item.path))?.name || 'Tổng quan'}
            </h1>
          </div>

          {/* Header Controls */}
          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <button className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 transition-colors relative focus:outline-none">
              <BellIcon className="w-5.5 h-5.5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-indigo-500 rounded-full"></span>
            </button>

            {/* Profile */}
            <div className="h-8 w-px bg-slate-800"></div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-medium text-slate-300 hidden md:block">{user?.email || 'admin@ecommerce.com'}</span>
              <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-white font-bold text-xs">
                {user?.username?.substring(0, 1).toUpperCase() || 'A'}
              </div>
            </div>
          </div>
        </header>

        {/* Outlet for Inner Pages */}
        <main className="flex-1 p-6 md:p-8 bg-slate-900">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
