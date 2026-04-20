import { useState, useEffect } from 'react';
import { getProvinces, getDistricts, getWards } from '../../data/vietnamLocations';

const AddressForm = ({ initialData = {}, onSubmit, onCancel, saving = false, submitText = 'Lưu địa chỉ' }) => {
  const [formData, setFormData] = useState({
    recipient_name: '',
    phone: '',
    province: '',
    district: '',
    ward: '',
    street_address: '',
    address_type: 'home',
    is_default: false,
    ...initialData
  });

  const [districts, setDistricts] = useState([]);
  const [wards, setWards] = useState([]);

  // Load districts when province changes
  useEffect(() => {
    if (formData.province) {
      const districtList = getDistricts(formData.province);
      setDistricts(districtList);

      // Reset district and ward if province changed
      if (initialData.province !== formData.province) {
        setFormData(prev => ({ ...prev, district: '', ward: '' }));
        setWards([]);
      }
    } else {
      setDistricts([]);
      setWards([]);
    }
  }, [formData.province]);

  // Load wards when district changes
  useEffect(() => {
    if (formData.province && formData.district) {
      const wardList = getWards(formData.province, formData.district);
      setWards(wardList);

      // Reset ward if district changed
      if (initialData.district !== formData.district) {
        setFormData(prev => ({ ...prev, ward: '' }));
      }
    } else {
      setWards([]);
    }
  }, [formData.district, formData.province]);

  // Initialize districts and wards for edit mode
  useEffect(() => {
    if (initialData.province) {
      setDistricts(getDistricts(initialData.province));
      if (initialData.district) {
        setWards(getWards(initialData.province, initialData.district));
      }
    }
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const provinces = getProvinces();

  return (
    <form onSubmit={handleSubmit}>
      <div className="grid md:grid-cols-2 gap-4">
        {/* Họ và tên */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Họ và tên <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="recipient_name"
            value={formData.recipient_name}
            onChange={handleChange}
            className="input"
            placeholder="Nguyễn Văn A"
            required
          />
        </div>

        {/* Số điện thoại */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Số điện thoại <span className="text-red-500">*</span>
          </label>
          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            className="input"
            placeholder="0912345678"
            required
          />
        </div>

        {/* Tỉnh/Thành phố */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tỉnh/Thành phố <span className="text-red-500">*</span>
          </label>
          <select
            name="province"
            value={formData.province}
            onChange={handleChange}
            className="input"
            required
          >
            <option value="">-- Chọn Tỉnh/Thành phố --</option>
            {provinces.map(province => (
              <option key={province} value={province}>{province}</option>
            ))}
          </select>
        </div>

        {/* Quận/Huyện */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Quận/Huyện <span className="text-red-500">*</span>
          </label>
          <select
            name="district"
            value={formData.district}
            onChange={handleChange}
            className="input"
            required
            disabled={!formData.province}
          >
            <option value="">-- Chọn Quận/Huyện --</option>
            {districts.map(district => (
              <option key={district} value={district}>{district}</option>
            ))}
          </select>
        </div>

        {/* Phường/Xã */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Phường/Xã <span className="text-red-500">*</span>
          </label>
          <select
            name="ward"
            value={formData.ward}
            onChange={handleChange}
            className="input"
            required
            disabled={!formData.district}
          >
            <option value="">-- Chọn Phường/Xã --</option>
            {wards.map(ward => (
              <option key={ward} value={ward}>{ward}</option>
            ))}
          </select>
        </div>

        {/* Loại địa chỉ */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Loại địa chỉ</label>
          <select
            name="address_type"
            value={formData.address_type}
            onChange={handleChange}
            className="input"
          >
            <option value="home">Nhà riêng</option>
            <option value="office">Văn phòng</option>
            <option value="other">Khác</option>
          </select>
        </div>

        {/* Địa chỉ chi tiết */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Địa chỉ chi tiết <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="street_address"
            value={formData.street_address}
            onChange={handleChange}
            className="input"
            placeholder="Số nhà, tên đường, tòa nhà..."
            required
          />
        </div>

        {/* Đặt làm mặc định */}
        <div className="md:col-span-2">
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              name="is_default"
              checked={formData.is_default}
              onChange={handleChange}
              className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
            />
            <span className="ml-2 text-sm text-gray-700">Đặt làm địa chỉ mặc định</span>
          </label>
        </div>
      </div>

      {/* Buttons */}
      <div className="flex justify-end space-x-3 mt-6">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary">
            Hủy
          </button>
        )}
        <button type="submit" disabled={saving} className="btn-primary">
          {saving ? 'Đang lưu...' : submitText}
        </button>
      </div>
    </form>
  );
};

export default AddressForm;
