import { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import userService from '../services/userService';
import { UserIcon, MapPinIcon, HeartIcon, BellIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const ProfilePage = () => {
  const { user } = useSelector((state) => state.auth);
  const [activeTab, setActiveTab] = useState('profile');
  const [profile, setProfile] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [profileRes, addressRes] = await Promise.all([
        userService.getProfile(),
        userService.getAddresses(),
      ]);
      setProfile(profileRes);
      setAddresses(addressRes);
    } catch (error) {
      toast.error('Lỗi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Thông tin cá nhân', icon: UserIcon },
    { id: 'addresses', label: 'Sổ địa chỉ', icon: MapPinIcon },
    { id: 'wishlist', label: 'Yêu thích', icon: HeartIcon },
    { id: 'notifications', label: 'Thông báo', icon: BellIcon },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">Tài khoản của tôi</h1>

      <div className="grid lg:grid-cols-4 gap-8">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="card p-4">
            <div className="flex items-center space-x-3 mb-6 pb-6 border-b">
              <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                <UserIcon className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">{user?.email?.split('@')[0]}</p>
                <p className="text-sm text-gray-500">{user?.email}</p>
              </div>
            </div>

            <nav className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left ${
                    activeTab === tab.id
                      ? 'bg-primary-50 text-primary-600'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          <div className="card p-6">
            {activeTab === 'profile' && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Thông tin cá nhân</h2>
                {loading ? (
                  <p>Đang tải...</p>
                ) : (
                  <form className="space-y-4 max-w-lg">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Họ và tên</label>
                      <input
                        type="text"
                        defaultValue={profile?.full_name}
                        className="input"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                      <input
                        type="email"
                        value={user?.email}
                        disabled
                        className="input bg-gray-50"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Số điện thoại</label>
                      <input
                        type="tel"
                        defaultValue={user?.phone}
                        className="input"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Giới tính</label>
                      <select defaultValue={profile?.gender} className="input">
                        <option value="">Chọn giới tính</option>
                        <option value="male">Nam</option>
                        <option value="female">Nữ</option>
                        <option value="other">Khác</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Ngày sinh</label>
                      <input
                        type="date"
                        defaultValue={profile?.date_of_birth}
                        className="input"
                      />
                    </div>
                    <button type="submit" className="btn-primary">
                      Lưu thay đổi
                    </button>
                  </form>
                )}
              </div>
            )}

            {activeTab === 'addresses' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold text-gray-900">Sổ địa chỉ</h2>
                  <button className="btn-primary text-sm">+ Thêm địa chỉ</button>
                </div>

                {addresses.length === 0 ? (
                  <p className="text-gray-500">Chưa có địa chỉ nào</p>
                ) : (
                  <div className="space-y-4">
                    {addresses.map((addr) => (
                      <div key={addr.id} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium">{addr.recipient_name}</p>
                            <p className="text-gray-600">{addr.phone}</p>
                            <p className="text-gray-600 text-sm mt-1">
                              {addr.street_address}, {addr.ward}, {addr.district}, {addr.province}
                            </p>
                          </div>
                          {addr.is_default && (
                            <span className="badge-success">Mặc định</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'wishlist' && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Sản phẩm yêu thích</h2>
                <p className="text-gray-500">Chưa có sản phẩm yêu thích</p>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Thông báo</h2>
                <p className="text-gray-500">Không có thông báo mới</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
