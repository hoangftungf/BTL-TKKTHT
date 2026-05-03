import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Link } from 'react-router-dom';
import userService from '../services/userService';
import productService from '../services/productService';
import AddressForm from '../components/address/AddressForm';
import { removeFromWishlist } from '../store/slices/wishlistSlice';
import { addToCart } from '../store/slices/cartSlice';
import { UserIcon, MapPinIcon, HeartIcon, BellIcon, PencilIcon, TrashIcon, PlusIcon, ShoppingCartIcon } from '@heroicons/react/24/outline';
import { formatPrice } from '../utils/format';
import toast from 'react-hot-toast';

const ProfilePage = () => {
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const { items: wishlistItems } = useSelector((state) => state.wishlist);
  const [activeTab, setActiveTab] = useState('profile');
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
                        setEditingAddress(null);
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
                    <AddressForm
                      initialData={editingAddress || {}}
                      onSubmit={handleAddressSubmit}
                      onCancel={resetAddressForm}
                      saving={saving}
                      submitText={editingAddress ? 'Cập nhật' : 'Thêm địa chỉ'}
                    />
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
                <h2 className="text-lg font-semibold text-gray-900 mb-6">
                  San pham yeu thich ({wishlistProducts.length})
                </h2>
                {loadingWishlist ? (
                  <p className="text-center py-8">Dang tai...</p>
                ) : wishlistProducts.length === 0 ? (
                  <div className="text-center py-12 bg-gray-50 rounded-lg">
                    <HeartIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 mb-4">Chua co san pham yeu thich</p>
                    <Link to="/products" className="btn-primary">
                      Kham pha san pham
                    </Link>
                  </div>
                ) : (
                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {wishlistProducts.map((product) => (
                      <div key={product.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                        <Link to={`/products/${product.id}`}>
                          <img
                            src={product.primary_image?.image || '/placeholder.png'}
                            alt={product.name}
                            className="w-full h-40 object-cover rounded-lg mb-3"
                          />
                          <h3 className="font-medium text-gray-900 line-clamp-2 mb-2 hover:text-primary-600">
                            {product.name}
                          </h3>
                        </Link>
                        <p className="text-lg font-bold text-red-600 mb-3">
                          {formatPrice(product.price)}
                        </p>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => {
                              dispatch(addToCart({ productId: product.id, quantity: 1 }))
                                .unwrap()
                                .then(() => toast.success('Da them vao gio hang'))
                                .catch((err) => toast.error(err));
                            }}
                            className="flex-1 btn-primary text-sm flex items-center justify-center"
                          >
                            <ShoppingCartIcon className="w-4 h-4 mr-1" />
                            Them vao gio
                          </button>
                          <button
                            onClick={() => {
                              dispatch(removeFromWishlist(product.id))
                                .unwrap()
                                .then(() => toast.success('Da xoa khoi yeu thich'))
                                .catch((err) => toast.error(err));
                            }}
                            className="p-2 text-red-500 hover:bg-red-50 rounded border border-red-200"
                            title="Xoa khoi yeu thich"
                          >
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
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
