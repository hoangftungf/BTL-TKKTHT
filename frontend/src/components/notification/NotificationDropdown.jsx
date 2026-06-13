import { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import notificationService from '../../services/notificationService';
import { 
  Bell, 
  ShoppingBag, 
  CreditCard, 
  Truck, 
  Gift, 
  Check, 
  Trash2,
  AlertCircle
} from 'lucide-react';
import toast from 'react-hot-toast';

const NotificationDropdown = ({ theme = 'light' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [activeFilter, setActiveFilter] = useState('all'); // 'all', 'unread'
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const data = await notificationService.getNotifications();
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
    // Poll every 30 seconds for new notifications
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markRead({ all: true });
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
      toast.success('Đã đánh dấu đọc tất cả thông báo');
    } catch (err) {
      console.error(err);
      toast.error('Không thể đánh dấu đọc tất cả');
    }
  };

  const handleNotificationClick = async (notif) => {
    setIsOpen(false);
    
    // Mark as read in backend
    if (!notif.is_read) {
      try {
        await notificationService.markRead({ ids: [notif.id] });
        setNotifications(prev => prev.map(n => n.id === notif.id ? { ...n, is_read: true } : n));
        setUnreadCount(prev => Math.max(0, prev - 1));
      } catch (err) {
        console.error(err);
      }
    }

    // Redirect based on type/data
    const orderId = notif.data?.order_id;
    const isStaff = theme === 'dark'; // Admin layout uses dark theme
    
    if (orderId) {
      if (isStaff) {
        navigate('/admin-dashboard/orders');
      } else {
        navigate('/orders');
      }
    }
  };

  const handleDeleteNotification = async (e, id) => {
    e.stopPropagation();
    try {
      await notificationService.deleteNotification(id);
      const deleted = notifications.find(n => n.id === id);
      setNotifications(prev => prev.filter(n => n.id !== id));
      if (deleted && !deleted.is_read) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
      toast.success('Đã xóa thông báo');
    } catch (err) {
      console.error(err);
      toast.error('Không thể xóa thông báo');
    }
  };

  // Filter notifications locally based on active filter state
  const displayedNotifications = useMemo(() => {
    if (activeFilter === 'unread') {
      return notifications.filter(n => !n.is_read);
    }
    return notifications;
  }, [notifications, activeFilter]);

  const getIcon = (type) => {
    switch (type) {
      case 'order':
        return <ShoppingBag className="w-4 h-4 text-blue-500" />;
      case 'payment':
        return <CreditCard className="w-4 h-4 text-emerald-500" />;
      case 'shipping':
        return <Truck className="w-4 h-4 text-purple-500" />;
      case 'promotion':
        return <Gift className="w-4 h-4 text-amber-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-indigo-500" />;
    }
  };

  const getIconBg = (type) => {
    switch (type) {
      case 'order':
        return 'bg-blue-500/10 border-blue-500/20';
      case 'payment':
        return 'bg-emerald-500/10 border-emerald-500/20';
      case 'shipping':
        return 'bg-purple-500/10 border-purple-500/20';
      case 'promotion':
        return 'bg-amber-500/10 border-amber-500/20';
      default:
        return 'bg-indigo-500/10 border-indigo-500/20';
    }
  };

  const formatTime = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Vừa xong';
    if (diffMins < 60) return `${diffMins} phút trước`;
    if (diffHours < 24) return `${diffHours} giờ trước`;
    if (diffDays < 7) return `${diffDays} ngày trước`;
    return date.toLocaleDateString('vi-VN');
  };

  const isDark = theme === 'dark';

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className={`p-2 rounded-xl transition-all relative flex items-center justify-center ${
          isDark 
            ? 'text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent' 
            : 'text-slate-600 hover:text-sky-400 hover:bg-slate-50 border border-transparent'
        }`}
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 bg-rose-500 text-white text-[9px] font-black w-5 h-5 rounded-full flex items-center justify-center border border-white animate-pulse">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className={`absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl shadow-2xl border z-50 flex flex-col overflow-hidden ${
          isDark 
            ? 'bg-slate-950 border-slate-800 text-white' 
            : 'bg-white border-slate-100 text-slate-800'
        }`}>
          {/* Header */}
          <div className={`flex items-center justify-between px-4 py-3 border-b shrink-0 ${
            isDark ? 'border-slate-800 bg-slate-900/40' : 'border-slate-100 bg-slate-50/50'
          }`}>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Thông báo</h3>
            {unreadCount > 0 && (
              <button 
                onClick={handleMarkAllRead}
                className="flex items-center gap-1 text-[10px] font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                <Check className="w-3.5 h-3.5" />
                Đọc tất cả
              </button>
            )}
          </div>

          {/* Filter tabs */}
          <div className={`flex gap-2 px-4 py-2 border-b shrink-0 ${
            isDark ? 'border-slate-900 bg-slate-950/20' : 'border-slate-100 bg-slate-50/30'
          }`}>
            <button
              onClick={() => setActiveFilter('all')}
              className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-wide transition-all ${
                activeFilter === 'all'
                  ? isDark ? 'bg-indigo-650 text-white' : 'bg-slate-900 text-white'
                  : isDark ? 'bg-slate-900 text-slate-400 hover:text-slate-200' : 'bg-slate-100 text-slate-550 hover:text-slate-800'
              }`}
            >
              Tất cả ({notifications.length})
            </button>
            <button
              onClick={() => setActiveFilter('unread')}
              className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-wide transition-all ${
                activeFilter === 'unread'
                  ? isDark ? 'bg-indigo-650 text-white' : 'bg-slate-900 text-white'
                  : isDark ? 'bg-slate-900 text-slate-400 hover:text-slate-200' : 'bg-slate-100 text-slate-550 hover:text-slate-800'
              }`}
            >
              Chưa đọc ({unreadCount})
            </button>
          </div>

          {/* List */}
          <div className="max-h-96 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-900/60 custom-scrollbar">
            {loading && notifications.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500">Đang tải...</div>
            ) : displayedNotifications.length === 0 ? (
              <div className="text-center py-12">
                <Bell className="w-8 h-8 text-slate-400 mx-auto mb-2 opacity-50" />
                <p className="text-xs text-slate-500">Không có thông báo nào</p>
              </div>
            ) : (
              displayedNotifications.map((notif) => (
                <div 
                  key={notif.id}
                  onClick={() => handleNotificationClick(notif)}
                  className={`flex items-start gap-3 p-3 text-left transition-colors cursor-pointer group relative ${
                    notif.is_read 
                      ? isDark ? 'hover:bg-slate-900/40' : 'hover:bg-slate-50'
                      : isDark ? 'bg-slate-900/30 hover:bg-slate-900/50' : 'bg-sky-50/20 hover:bg-sky-50/40'
                  }`}
                >
                  {/* Icon */}
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border ${getIconBg(notif.type)}`}>
                    {getIcon(notif.type)}
                  </div>

                  {/* Body */}
                  <div className="flex-1 min-w-0 pr-6">
                    <p className={`text-xs truncate font-bold ${
                      notif.is_read ? 'text-slate-350 dark:text-slate-400' : 'text-slate-900 dark:text-slate-150'
                    }`}>
                      {notif.title}
                    </p>
                    <p className="text-[11px] text-slate-550 dark:text-slate-400 mt-0.5 leading-snug line-clamp-2">
                      {notif.message}
                    </p>
                    <span className="text-[9px] text-slate-400 mt-1 block font-medium">
                      {formatTime(notif.created_at)}
                    </span>
                  </div>

                  {/* Action overlay: delete / unread marker */}
                  <div className="absolute right-3 top-3 flex items-center gap-1.5">
                    {!notif.is_read && (
                      <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full shrink-0 group-hover:hidden" />
                    )}
                    <button
                      onClick={(e) => handleDeleteNotification(e, notif.id)}
                      className="text-slate-400 hover:text-red-500 p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {unreadCount > 0 && (
            <div className={`px-4 py-2.5 text-center border-t shrink-0 ${
              isDark ? 'border-slate-800 bg-slate-900/30' : 'border-slate-100 bg-slate-50/30'
            }`}>
              <button
                onClick={handleMarkAllRead}
                className="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 transition-colors uppercase tracking-wider"
              >
                Đánh dấu đã đọc tất cả
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationDropdown;
