import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import userService from '../../services/userService';
import {
  UsersIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  UserMinusIcon,
  UserPlusIcon
} from '@heroicons/react/24/outline';

const AdminUsersPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  // Form edit state
  const [updatingUserId, setUpdatingUserId] = useState(null);

  useEffect(() => {
    fetchUsers();
  }, [roleFilter]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await userService.getAdminUsers();
      
      let filteredUsers = data || [];
      
      // Filter by role
      if (roleFilter) {
        filteredUsers = filteredUsers.filter(u => u.role === roleFilter);
      }
      
      // Filter by search query (email or phone)
      if (searchQuery.trim()) {
        filteredUsers = filteredUsers.filter(u => 
          (u.email && u.email.toLowerCase().includes(searchQuery.toLowerCase())) ||
          (u.phone && u.phone.includes(searchQuery))
        );
      }

      setUsers(filteredUsers);
    } catch (error) {
      console.error('Fetch users error:', error);
      toast.error('Không thể tải danh sách thành viên');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchUsers();
  };

  const handleRoleChange = async (userId, newRole) => {
    setUpdatingUserId(userId);
    const loadingToast = toast.loading(`Đang cập nhật vai trò sang ${newRole}...`);
    try {
      await userService.updateAdminUser(userId, { role: newRole });
      toast.success('Cập nhật vai trò thành công!', { id: loadingToast });
      fetchUsers();
    } catch (error) {
      console.error('Change role error:', error);
      toast.error(error.response?.data?.error || 'Không thể thay đổi vai trò người dùng', { id: loadingToast });
    } finally {
      setUpdatingUserId(null);
    }
  };

  const handleToggleStatus = async (userId, currentStatus) => {
    setUpdatingUserId(userId);
    const newStatus = !currentStatus;
    const loadingToast = toast.loading(newStatus ? 'Đang kích hoạt tài khoản...' : 'Đang khóa tài khoản...');
    try {
      await userService.updateAdminUser(userId, { is_active: newStatus });
      toast.success(newStatus ? 'Đã kích hoạt tài khoản thành công!' : 'Đã khóa tài khoản thành công!', { id: loadingToast });
      fetchUsers();
    } catch (error) {
      console.error('Toggle status error:', error);
      toast.error('Không thể thay đổi trạng thái tài khoản', { id: loadingToast });
    } finally {
      setUpdatingUserId(null);
    }
  };

  const getRoleBadgeClass = (role) => {
    switch (role) {
      case 'admin':
        return 'bg-rose-950/20 text-rose-400 border-rose-900/40';
      case 'seller':
        return 'bg-amber-950/20 text-amber-400 border-amber-900/40';
      default:
        return 'bg-blue-950/20 text-blue-400 border-blue-900/40';
    }
  };

  const getRoleDisplay = (role) => {
    switch (role) {
      case 'admin': return 'Admin';
      case 'seller': return 'Seller';
      default: return 'Customer';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800/80 shadow-xl">
        <h2 className="text-2xl font-bold text-white tracking-wide">Quản lý Thành viên</h2>
        <p className="text-slate-400 text-sm mt-0.5">Danh sách toàn bộ thành viên hệ thống. Cho phép phân quyền vai trò (Admin, Seller, Customer) hoặc khóa tài khoản.</p>
      </div>

      {/* Filters Bar */}
      <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/60 flex flex-col md:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:max-w-xs">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm theo email hoặc SĐT..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <MagnifyingGlassIcon className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-500" />
        </form>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center space-x-2 bg-slate-900 px-3 py-2 rounded-xl border border-slate-800 w-full md:w-auto">
            <ShieldCheckIcon className="w-4 h-4 text-slate-500" />
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="bg-transparent text-xs text-slate-300 font-semibold focus:outline-none border-none pr-6 cursor-pointer"
            >
              <option value="" className="bg-slate-900">Tất cả vai trò</option>
              <option value="customer" className="bg-slate-900">Customer (Khách hàng)</option>
              <option value="seller" className="bg-slate-900">Seller (Người bán)</option>
              <option value="admin" className="bg-slate-900">Admin (Quản trị)</option>
            </select>
          </div>

          <button 
            onClick={() => {
              setSearchQuery('');
              setRoleFilter('');
            }}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors focus:outline-none"
            title="Làm mới bộ lọc"
          >
            <ArrowPathIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Users List Table */}
      <div className="bg-slate-950 rounded-2xl border border-slate-800/80 shadow-xl overflow-hidden">
        {loading ? (
          <div className="p-20 flex flex-col items-center justify-center space-y-4">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-indigo-500"></div>
            <p className="text-slate-400 text-sm">Đang tải danh sách thành viên...</p>
          </div>
        ) : users.length === 0 ? (
          <div className="p-20 text-center space-y-2">
            <UsersIcon className="w-12 h-12 text-slate-700 mx-auto" />
            <p className="text-slate-400 text-sm font-medium">Không tìm thấy thành viên nào</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-950 border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <th className="py-4 px-6">Email / Liên hệ</th>
                  <th className="py-4 px-6">Số điện thoại</th>
                  <th className="py-4 px-6">Ngày tham gia</th>
                  <th className="py-4 px-6">Vai trò</th>
                  <th className="py-4 px-6">Trạng thái</th>
                  <th className="py-4 px-6 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850">
                {users.map((userItem) => (
                  <tr key={userItem.id} className="hover:bg-slate-900/35 transition-colors">
                    <td className="py-4 px-6">
                      <div className="flex items-center space-x-3">
                        <div className="w-9 h-9 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center font-bold text-indigo-400 text-xs">
                          {userItem.email?.substring(0, 2).toUpperCase() || 'US'}
                        </div>
                        <div className="min-w-0">
                          <span className="font-semibold text-white text-sm block truncate">{userItem.email}</span>
                          <span className="text-[10px] text-slate-500 font-mono block truncate">{userItem.id}</span>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-sm text-slate-300 font-medium">
                      {userItem.phone || 'N/A'}
                    </td>
                    <td className="py-4 px-6 text-xs text-slate-400 font-medium">
                      {new Date(userItem.created_at).toLocaleDateString('vi-VN', {
                        year: 'numeric', month: 'long', day: 'numeric'
                      })}
                    </td>
                    <td className="py-4 px-6">
                      <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border uppercase tracking-wider ${getRoleBadgeClass(userItem.role)}`}>
                        {getRoleDisplay(userItem.role)}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider border ${
                        userItem.is_active 
                          ? 'bg-emerald-950/20 text-emerald-400 border-emerald-900/40' 
                          : 'bg-rose-950/20 text-rose-400 border-rose-900/40'
                      }`}>
                        {userItem.is_active ? 'Hoạt động' : 'Đã khóa'}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        {/* Change Role selection */}
                        <select
                          disabled={updatingUserId === userItem.id}
                          value={userItem.role}
                          onChange={(e) => handleRoleChange(userItem.id, e.target.value)}
                          className="bg-slate-900 border border-slate-800 text-slate-300 text-xs py-1 px-2.5 rounded-lg focus:outline-none focus:border-indigo-500 cursor-pointer disabled:opacity-40"
                        >
                          <option value="customer">Làm Khách hàng</option>
                          <option value="seller">Làm Người bán</option>
                          <option value="admin">Làm Admin</option>
                        </select>

                        {/* Block / Unblock toggle */}
                        <button
                          disabled={updatingUserId === userItem.id}
                          onClick={() => handleToggleStatus(userItem.id, userItem.is_active)}
                          className={`p-1.5 rounded-lg border transition-colors focus:outline-none disabled:opacity-40 ${
                            userItem.is_active 
                              ? 'text-rose-500 border-rose-950/20 hover:bg-rose-950/25 hover:text-rose-400' 
                              : 'text-emerald-500 border-emerald-950/20 hover:bg-emerald-950/25 hover:text-emerald-400'
                          }`}
                          title={userItem.is_active ? 'Khóa tài khoản' : 'Mở khóa tài khoản'}
                        >
                          {userItem.is_active ? (
                            <UserMinusIcon className="w-4.5 h-4.5" />
                          ) : (
                            <UserPlusIcon className="w-4.5 h-4.5" />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminUsersPage;
