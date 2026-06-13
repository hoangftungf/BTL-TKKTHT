import { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Link, useLocation } from 'react-router-dom';
import userService from '../services/userService';
import productService from '../services/productService';
import AddressForm from '../components/address/AddressForm';
import ProductCard from '../components/product/ProductCard';
import { 
  UserIcon, 
  MapPinIcon, 
  HeartIcon, 
  PencilIcon, 
  TrashIcon, 
  PlusIcon 
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const ProfilePage = () => {
  const { user } = useSelector((state) => state.auth);
  const { items: wishlistItems } = useSelector((state) => state.wishlist);
  
  const location = useLocation();
  const [activeTab, setActiveTab] = useState(location.state?.activeTab || 'profile');
  const [profile, setProfile] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Wishlist product details
  const [wishlistProducts, setWishlistProducts] = useState([]);
  const [loadingWishlist, setLoadingWishlist] = useState(false);

  // Address form state
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);

  // Profile form state
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    gender: '',
    date_of_birth: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  // Load wishlist product details when wishlist items change
  useEffect(() => {
    const loadWishlistProducts = async () => {
      if (wishlistItems.length === 0) {
        setWishlistProducts([]);
        return;
      }
      setLoadingWishlist(true);
      try {
        const products = await Promise.all(
          wishlistItems.map(async (item) => {
            try {
              const product = await productService.getProductById(item.product_id);
              return product;
            } catch {
              return null;
            }
          })
        );
        setWishlistProducts(products.filter(Boolean));
      } catch (error) {
        console.error('Error loading wishlist products:', error);
      } finally {
        setLoadingWishlist(false);
      }
    };
    loadWishlistProducts();
  }, [wishlistItems]);

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

  useEffect(() => {
    if (location.state?.activeTab) {
      setActiveTab(location.state.activeTab);
    }
  }, [location.state]);

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
    setEditingAddress(null);
    setShowAddressForm(false);
  };

  const handleEditAddress = (address) => {
    setEditingAddress(address);
    setShowAddressForm(true);
  };

  const handleAddressSubmit = async (formData) => {
    setSaving(true);
    try {
      if (editingAddress) {
        const updated = await userService.updateAddress(editingAddress.id, formData);
        setAddresses(addresses.map(a => a.id === editingAddress.id ? updated : a));
        toast.success('Cập nhật địa chỉ thành công');
      } else {
        const created = await userService.addAddress(formData);
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
                  <form onSubmit={handleProfileSubmit} className="max-w-md space-y-4">
                    <div>
                      <label className="label">Họ và tên</label>
                      <input
                        type="text"
                        value={profileForm.full_name}
                        onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                        className="input"
                      />
                    </div>
                    <div>
                      <label className="label">Email</label>
                      <input
                        type="email"
                        value={user?.email || ''}
                        disabled
                        className="input bg-gray-50 cursor-not-allowed"
                      />
                    </div>
                    <div>
                      <label className="label">Giới tính</label>
                      <div className="flex space-x-4 mt-2">
                        <label className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="radio"
                            name="gender"
                            value="male"
                            checked={profileForm.gender === 'male'}
                            onChange={(e) => setProfileForm({ ...profileForm, gender: e.target.value })}
                            className="text-primary-650 focus:ring-primary-500"
                          />
                          <span>Nam</span>
                        </label>
                        <label className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="radio"
                            name="gender"
                            value="female"
                            checked={profileForm.gender === 'female'}
                            onChange={(e) => setProfileForm({ ...profileForm, gender: e.target.value })}
                            className="text-primary-650 focus:ring-primary-500"
                          />
                          <span>Nữ</span>
                        </label>
                        <label className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="radio"
                            name="gender"
                            value="other"
                            checked={profileForm.gender === 'other'}
                            onChange={(e) => setProfileForm({ ...profileForm, gender: e.target.value })}
                            className="text-primary-650 focus:ring-primary-500"
                          />
                          <span>Khác</span>
                        </label>
                      </div>
                    </div>
                    <div>
                      <label className="label">Ngày sinh</label>
                      <input
                        type="date"
                        value={profileForm.date_of_birth}
                        onChange={(e) => setProfileForm({ ...profileForm, date_of_birth: e.target.value })}
                        className="input"
                      />
                    </div>
                    <button type="submit" disabled={saving} className="btn-primary w-full">
                      {saving ? 'Đang lưu...' : 'Lưu thay đổi'}
                    </button>
                  </form>
                )}
              </div>
            )}

            {/* Addresses Tab */}
            {activeTab === 'addresses' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-lg font-semibold text-gray-900">Sổ địa chỉ</h2>
                  {!showAddressForm && (
                    <button onClick={() => setShowAddressForm(true)} className="btn-outline flex items-center space-x-1 py-1.5 text-sm">
                      <PlusIcon className="w-4 h-4" />
                      <span>Thêm địa chỉ mới</span>
                    </button>
                  )}
                </div>

                {showAddressForm ? (
                  <div className="bg-gray-50 p-4 rounded-lg border">
                    <h3 className="font-medium text-gray-900 mb-4">{editingAddress ? 'Chỉnh sửa địa chỉ' : 'Thêm địa chỉ mới'}</h3>
                    <AddressForm
                      initialData={editingAddress}
                      onSubmit={handleAddressSubmit}
                      onCancel={resetAddressForm}
                    />
                  </div>
                ) : loading ? (
                  <p>Đang tải...</p>
                ) : addresses.length === 0 ? (
                  <div className="text-center py-12 bg-gray-50 rounded-lg">
                    <MapPinIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">Chưa có địa chỉ nào</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {addresses.map((address) => (
                      <div key={address.id} className="p-4 bg-white border rounded-lg hover:shadow-sm transition-all flex justify-between items-start">
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold text-gray-950">{address.recipient_name}</span>
                            <span className="text-gray-400">|</span>
                            <span className="text-gray-600">{address.phone}</span>
                            {address.is_default && (
                              <span className="bg-primary-100 text-primary-800 text-[10px] px-2 py-0.5 rounded font-medium">Mặc định</span>
                            )}
                          </div>
                          <p className="text-gray-600 text-sm">
                            {address.street_address}, {address.ward}, {address.district}, {address.province}
                          </p>
                          {!address.is_default && (
                            <button onClick={() => handleSetDefault(address)} className="text-primary-600 hover:text-primary-850 text-xs font-semibold mt-2 block">
                              Đặt làm mặc định
                            </button>
                          )}
                        </div>

                        <div className="flex space-x-2 shrink-0">
                          <button onClick={() => handleEditAddress(address)} className="p-1 text-gray-500 hover:text-primary-600 rounded-md hover:bg-gray-50" title="Chỉnh sửa">
                            <PencilIcon className="w-4 h-4" />
                          </button>
                          <button onClick={() => handleDeleteAddress(address.id)} className="p-1 text-gray-500 hover:text-red-650 rounded-md hover:bg-gray-50" title="Xóa">
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </div>
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
                {loadingWishlist ? (
                  <p className="text-center py-8">Đang tải...</p>
                ) : wishlistProducts.length === 0 ? (
                  <div className="text-center py-12 bg-gray-50 rounded-lg">
                    <HeartIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 mb-4">Chưa có sản phẩm yêu thích</p>
                    <Link to="/products" className="btn-primary">
                      Khám phá sản phẩm
                    </Link>
                  </div>
                ) : (
                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {wishlistProducts.map((product) => (
                      <ProductCard key={product.id} product={product} />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
