import { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import userService from '../services/userService';
import { UserIcon, MapPinIcon, HeartIcon, BellIcon, PencilIcon, TrashIcon, PlusIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const ProfilePage = () => {
  const { user } = useSelector((state) => state.auth);
  const [activeTab, setActiveTab] = useState('profile');
  const [profile, setProfile] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Address form state
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);
  const [addressForm, setAddressForm] = useState({
    recipient_name: '',
    phone: '',
    province: '',
    district: '',
    ward: '',
    street_address: '',
    address_type: 'home',
    is_default: false,
  });

  // Profile form state
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    gender: '',
    date_of_birth: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (profile) {
      setProfileForm({
        full_name: profile.full_name || '',
        gender: profile.gender || '',
        date_of_birth: profile.date_of_birth || '',
      });
    }
  }, [profile]);

  const loadData = async () => {
    try {
      const [profileRes, addressRes] = await Promise.all([
        userService.getProfile(),
        userService.getAddresses(),
      ]);
      setProfile(profileRes);
      setAddresses(addressRes);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await userService.updateProfile(profileForm);
      setProfile(updated);
      toast.success('Cập nhật thông tin thành công');
    } catch (error) {
      toast.error('Không thể cập nhật thông tin');
    } finally {
      setSaving(false);
    }
  };

  const resetAddressForm = () => {
    setAddressForm({
      recipient_name: '',
      phone: '',
      province: '',
      district: '',
      ward: '',
      street_address: '',
      address_type: 'home',
      is_default: false,
    });
    setEditingAddress(null);
    setShowAddressForm(false);
  };

  const handleEditAddress = (address) => {
    setEditingAddress(address);
    setAddressForm({
      recipient_name: address.recipient_name,
      phone: address.phone,
      province: address.province,
      district: address.district,
      ward: address.ward,
      street_address: address.street_address,
      address_type: address.address_type,
      is_default: address.is_default,
    });
    setShowAddressForm(true);
  };

  const handleAddressSubmit = async (e) => {
    e.preventDefault();

    if (!addressForm.recipient_name || !addressForm.phone || !addressForm.street_address) {
      toast.error('Vui lòng điền đầy đủ thông tin');
      return;
    }

    setSaving(true);
    try {
      if (editingAddress) {
        const updated = await userService.updateAddress(editingAddress.id, addressForm);
        setAddresses(addresses.map(a => a.id === editingAddress.id ? updated : a));
        toast.success('Cập nhật địa chỉ thành công');
      } else {
        const created = await userService.addAddress(addressForm);
        setAddresses([...addresses, created]);
        toast.success('Thêm địa chỉ thành công');
      }
      resetAddressForm();
    } catch (error) {
      toast.error('Không thể lưu địa chỉ');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteAddress = async (addressId) => {
    if (!window.confirm('Bạn có chắc muốn xóa địa chỉ này?')) return;

    try {
      await userService.deleteAddress(addressId);
      setAddresses(addresses.filter(a => a.id !== addressId));
      toast.success('Xóa địa chỉ thành công');
    } catch (error) {
      toast.error('Không thể xóa địa chỉ');
    }
  };

  const handleSetDefault = async (address) => {
    try {
      await userService.updateAddress(address.id, { ...address, is_default: true });
      setAddresses(addresses.map(a => ({
        ...a,
        is_default: a.id === address.id
      })));
      toast.success('Đã đặt làm địa chỉ mặc định');
    } catch (error) {
      toast.error('Không thể cập nhật');
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
                <p className="font-medium text-gray-900">{profile?.full_name || user?.email?.split('@')[0]}</p>
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
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Thông tin cá nhân</h2>
                {loading ? (
                  <p>Đang tải...</p>
                ) : (
                  <form onSubmit={handleProfileSubmit} className="space-y-4 max-w-lg">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Họ và tên</label>
                      <input
                        type="text"
                        value={profileForm.full_name}
                        onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                        className="input"
                        placeholder="Nhập họ và tên"
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
                      <label className="block text-sm font-medium text-gray-700 mb-1">Giới tính</label>
                      <select
                        value={profileForm.gender}
                        onChange={(e) => setProfileForm({ ...profileForm, gender: e.target.value })}
                        className="input"
                      >
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
                        value={profileForm.date_of_birth}
                        onChange={(e) => setProfileForm({ ...profileForm, date_of_birth: e.target.value })}
                        className="input"
                      />
                    </div>
                    <button type="submit" disabled={saving} className="btn-primary">
                      {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
                    </button>
                  </form>
                )}
              </div>
            )}

            {/* Addresses Tab */}
            {activeTab === 'addresses' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold text-gray-900">Sổ địa chỉ</h2>
                  {!showAddressForm && (
                    <button
                      onClick={() => {
                        resetAddressForm();
                        setShowAddressForm(true);
                      }}
                      className="btn-primary text-sm flex items-center"
                    >
                      <PlusIcon className="w-4 h-4 mr-1" />
                      Thêm địa chỉ
                    </button>
                  )}
                </div>

                {/* Address Form */}
                {showAddressForm && (
                  <div className="border-2 border-dashed border-primary-300 rounded-lg p-4 mb-6 bg-primary-50">
                    <h3 className="font-medium text-gray-900 mb-4">
                      {editingAddress ? 'Sửa địa chỉ' : 'Thêm địa chỉ mới'}
                    </h3>
                    <form onSubmit={handleAddressSubmit}>
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Họ và tên *</label>
                          <input
                            type="text"
                            value={addressForm.recipient_name}
                            onChange={(e) => setAddressForm({ ...addressForm, recipient_name: e.target.value })}
                            className="input"
                            placeholder="Nguyễn Văn A"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Số điện thoại *</label>
                          <input
                            type="tel"
                            value={addressForm.phone}
                            onChange={(e) => setAddressForm({ ...addressForm, phone: e.target.value })}
                            className="input"
                            placeholder="0912345678"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Tỉnh/Thành phố *</label>
                          <input
                            type="text"
                            value={addressForm.province}
                            onChange={(e) => setAddressForm({ ...addressForm, province: e.target.value })}
                            className="input"
                            placeholder="Hà Nội"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Quận/Huyện *</label>
                          <input
                            type="text"
                            value={addressForm.district}
                            onChange={(e) => setAddressForm({ ...addressForm, district: e.target.value })}
                            className="input"
                            placeholder="Cầu Giấy"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Phường/Xã *</label>
                          <input
                            type="text"
                            value={addressForm.ward}
                            onChange={(e) => setAddressForm({ ...addressForm, ward: e.target.value })}
                            className="input"
                            placeholder="Dịch Vọng"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Loại địa chỉ</label>
                          <select
                            value={addressForm.address_type}
                            onChange={(e) => setAddressForm({ ...addressForm, address_type: e.target.value })}
                            className="input"
                          >
                            <option value="home">Nhà riêng</option>
                            <option value="office">Văn phòng</option>
                            <option value="other">Khác</option>
                          </select>
                        </div>
                        <div className="md:col-span-2">
                          <label className="block text-sm font-medium text-gray-700 mb-1">Địa chỉ chi tiết *</label>
                          <input
                            type="text"
                            value={addressForm.street_address}
                            onChange={(e) => setAddressForm({ ...addressForm, street_address: e.target.value })}
                            className="input"
                            placeholder="Số nhà, tên đường..."
                          />
                        </div>
                        <div className="md:col-span-2">
                          <label className="flex items-center">
                            <input
                              type="checkbox"
                              checked={addressForm.is_default}
                              onChange={(e) => setAddressForm({ ...addressForm, is_default: e.target.checked })}
                              className="mr-2"
                            />
                            <span className="text-sm text-gray-700">Đặt làm địa chỉ mặc định</span>
                          </label>
                        </div>
                      </div>
                      <div className="flex justify-end space-x-3 mt-4">
                        <button type="button" onClick={resetAddressForm} className="btn-secondary">
                          Hủy
                        </button>
                        <button type="submit" disabled={saving} className="btn-primary">
                          {saving ? 'Đang lưu...' : (editingAddress ? 'Cập nhật' : 'Thêm địa chỉ')}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {/* Address List */}
                {addresses.length === 0 && !showAddressForm ? (
                  <div className="text-center py-12 bg-gray-50 rounded-lg">
                    <MapPinIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 mb-4">Bạn chưa có địa chỉ nào</p>
                    <button
                      onClick={() => setShowAddressForm(true)}
                      className="btn-primary"
                    >
                      Thêm địa chỉ đầu tiên
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {addresses.map((addr) => (
                      <div key={addr.id} className="border rounded-lg p-4 hover:border-primary-300 transition-colors">
                        <div className="flex items-start justify-between">
                          <div className="flex-grow">
                            <div className="flex items-center flex-wrap gap-2 mb-1">
                              <span className="font-medium text-gray-900">{addr.recipient_name}</span>
                              <span className="text-gray-300">|</span>
                              <span className="text-gray-600">{addr.phone}</span>
                              {addr.is_default && (
                                <span className="px-2 py-0.5 bg-primary-100 text-primary-700 text-xs rounded">
                                  Mặc định
                                </span>
                              )}
                              <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                                {addr.address_type === 'home' ? 'Nhà riêng' : addr.address_type === 'office' ? 'Văn phòng' : 'Khác'}
                              </span>
                            </div>
                            <p className="text-gray-600 text-sm">
                              {addr.street_address}, {addr.ward}, {addr.district}, {addr.province}
                            </p>
                          </div>
                          <div className="flex items-center space-x-2 ml-4">
                            <button
                              onClick={() => handleEditAddress(addr)}
                              className="p-2 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded"
                              title="Sửa"
                            >
                              <PencilIcon className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteAddress(addr.id)}
                              className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded"
                              title="Xóa"
                            >
                              <TrashIcon className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                        {!addr.is_default && (
                          <button
                            onClick={() => handleSetDefault(addr)}
                            className="mt-2 text-sm text-primary-600 hover:text-primary-700"
                          >
                            Đặt làm mặc định
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Wishlist Tab */}
            {activeTab === 'wishlist' && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Sản phẩm yêu thích</h2>
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                  <HeartIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">Chưa có sản phẩm yêu thích</p>
                </div>
              </div>
            )}

            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Thông báo</h2>
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                  <BellIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">Không có thông báo mới</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
