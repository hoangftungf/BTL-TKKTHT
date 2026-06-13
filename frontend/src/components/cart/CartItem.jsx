import { Link } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { updateCartItem, removeCartItem } from '../../store/slices/cartSlice';
import { MinusIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import { formatPrice } from '../../utils/format';
import toast from 'react-hot-toast';

const CartItem = ({ item, isSelected, onToggleSelect }) => {
  const dispatch = useDispatch();

  const handleQuantityChange = (newQuantity) => {
    if (newQuantity < 1) return;
    dispatch(updateCartItem({ itemId: item.id, quantity: newQuantity }))
      .unwrap()
      .catch((err) => toast.error(err));
  };

  const handleRemove = () => {
    dispatch(removeCartItem(item.id))
      .unwrap()
      .then(() => toast.success('Đã xóa sản phẩm'))
      .catch((err) => toast.error(err));
  };

  const getAttributeLabel = (key) => {
    const labels = {
      ram: 'RAM',
      ssd: 'SSD',
      color: 'Màu',
      size: 'Size',
      material: 'Chất liệu',
      storage: 'Dung lượng'
    };
    return labels[key.toLowerCase()] || key;
  };

  return (
    <div className="flex flex-col md:flex-row md:items-center bg-white px-6 py-5 gap-4 hover:bg-gray-50/40 border-b border-gray-100 transition-colors duration-150">
      {/* Checkbox & Product Column */}
      <div className="flex items-center space-x-3.5 flex-grow basis-[45%] min-w-0">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggleSelect}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 h-4 w-4 cursor-pointer accent-blue-600"
        />
        
        <div className="flex items-center space-x-4 flex-grow min-w-0">
          {/* Image */}
          <Link to={`/products/${item.product_id}`} className="w-20 h-20 flex-shrink-0 rounded-lg overflow-hidden bg-gray-50 border border-gray-150 block hover:opacity-95 transition-opacity relative group">
            <img
              src={item.product_image || '/placeholder.png'}
              alt={item.product_name}
              className="w-full h-full object-cover group-hover:scale-102 transition-transform duration-200"
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = '/placeholder.png';
              }}
            />
          </Link>
          
          {/* Name & Badges */}
          <div className="flex-grow min-w-0 flex flex-col justify-between py-0.5">
            <Link to={`/products/${item.product_id}`} className="hover:text-blue-600 transition-colors">
              <h4 className="font-semibold text-gray-900 text-sm line-clamp-2 leading-relaxed">
                {item.product_name}
              </h4>
            </Link>
            
            <div className="flex flex-wrap gap-1.5 mt-2">
              <span className="bg-blue-50 text-blue-600 text-[9.5px] font-bold px-1.5 py-0.5 rounded border border-blue-100">
                Yêu thích
              </span>
              <span className="bg-orange-50 text-orange-600 text-[9.5px] font-bold px-1.5 py-0.5 rounded border border-orange-100">
                Voucher Xtra
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Variation Column */}
      <div className="w-full md:w-[18%] flex-shrink-0 flex md:justify-center items-center">
        {item.variant_info && item.variant_info.attributes && Object.keys(item.variant_info.attributes).length > 0 ? (
          <div className="text-xs text-gray-500 flex flex-col md:items-center gap-1.5 w-full">
            <span className="text-[10px] uppercase tracking-wider text-gray-400 font-bold md:text-center block">Phân loại</span>
            <div className="flex flex-wrap md:justify-center gap-1">
              {Object.entries(item.variant_info.attributes).map(([key, val]) => (
                <span 
                  key={key} 
                  className="bg-gray-50 text-gray-700 px-2 py-0.5 rounded border border-gray-200 text-[10.5px] font-medium"
                  title={`${getAttributeLabel(key)}: ${val}`}
                >
                  <span className="text-gray-400 mr-0.5">{getAttributeLabel(key)}:</span> {val}
                </span>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-xs text-gray-400 italic flex flex-col md:items-center gap-1 w-full">
            <span className="text-[10px] uppercase tracking-wider text-gray-400 font-bold md:text-center block">Phân loại</span>
            <span>Mặc định</span>
          </div>
        )}
      </div>

      {/* Unit Price Column */}
      <div className="w-full md:w-[12%] flex-shrink-0 text-left md:text-center flex md:flex-col justify-between md:justify-center items-center">
        <span className="md:hidden text-xs text-gray-400 font-medium">Đơn Giá:</span>
        <div className="flex flex-row md:flex-col items-center md:items-center gap-1.5">
          <span className="text-gray-900 text-sm font-semibold">{formatPrice(item.price)}</span>
        </div>
      </div>

      {/* Quantity Column */}
      <div className="w-full md:w-[12%] flex-shrink-0 flex md:justify-center items-center justify-between">
        <span className="md:hidden text-xs text-gray-400 font-medium">Số Lượng:</span>
        <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden h-8 bg-white shadow-sm">
          <button
            onClick={() => handleQuantityChange(item.quantity - 1)}
            disabled={item.quantity <= 1}
            className="w-7 h-full hover:bg-gray-100 disabled:opacity-40 flex items-center justify-center border-r border-gray-200 transition-colors"
          >
            <MinusIcon className="w-3.5 h-3.5 text-gray-600" />
          </button>
          <span className="w-9 text-center text-xs font-bold text-gray-800">{item.quantity}</span>
          <button
            onClick={() => handleQuantityChange(item.quantity + 1)}
            className="w-7 h-full hover:bg-gray-100 flex items-center justify-center border-l border-gray-200 transition-colors"
          >
            <PlusIcon className="w-3.5 h-3.5 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Subtotal Column */}
      <div className="w-full md:w-[12%] flex-shrink-0 text-right md:text-center flex md:justify-center justify-between items-center">
        <span className="md:hidden text-xs text-gray-400 font-medium">Số Tiền:</span>
        <span className="font-bold text-blue-600 text-[14.5px]">{formatPrice(item.subtotal)}</span>
      </div>

      {/* Actions Column */}
      <div className="w-full md:w-[8%] flex-shrink-0 text-right md:text-center flex md:flex-col justify-between md:justify-center items-end md:items-center">
        <span className="md:hidden text-xs text-gray-400 font-medium">Thao Tác:</span>
        <button
          onClick={handleRemove}
          className="text-gray-400 hover:text-red-500 p-1.5 rounded-full hover:bg-red-50 transition-all duration-150"
          title="Xóa sản phẩm"
        >
          <TrashIcon className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

export default CartItem;
