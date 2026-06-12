import { Link } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { updateCartItem, removeCartItem } from '../../store/slices/cartSlice';
import { MinusIcon, PlusIcon } from '@heroicons/react/24/outline';
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

  return (
    <div className="flex flex-col md:flex-row md:items-center bg-white px-6 py-5 gap-4 hover:bg-primary-50/10 transition-colors duration-150">
      {/* Checkbox & Product Column */}
      <div className="flex items-center space-x-3 flex-grow basis-[40%] min-w-0">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggleSelect}
          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 h-4.5 w-4.5 cursor-pointer accent-primary-600"
        />
        
        <div className="flex items-center space-x-3 flex-grow min-w-0">
          {/* Image */}
          <Link to={`/products/${item.product_id}`} className="w-20 h-20 flex-shrink-0 rounded-md overflow-hidden bg-gray-50 border border-gray-100 block hover:opacity-95 transition-opacity">
            <img
              src={item.product_image || '/placeholder.png'}
              alt={item.product_name}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = '/placeholder.png';
              }}
            />
          </Link>
          
          {/* Name & Badges */}
          <div className="flex-grow min-w-0 flex flex-col justify-between py-1">
            <Link to={`/products/${item.product_id}`} className="hover:text-primary-600 transition-colors">
              <h4 className="font-medium text-gray-900 text-sm line-clamp-2 leading-relaxed">
                {item.product_name}
              </h4>
            </Link>
            
            <div className="flex flex-wrap gap-1 mt-1.5">
              <span className="bg-primary-600 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-sm">
                Yêu thích
              </span>
              <span className="text-[9px] border border-primary-500 text-primary-600 px-1 py-0.5 rounded-sm font-semibold">
                15.6
              </span>
              <span className="text-[9px] border border-primary-500 text-primary-600 px-1 py-0.5 rounded-sm font-semibold">
                Voucher Xtra
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Variation Column */}
      <div className="w-full md:w-[18%] flex-shrink-0 flex md:justify-center items-center">
        <div className="relative group cursor-pointer text-xs text-gray-500 bg-gray-50 hover:bg-gray-100 hover:text-gray-700 border border-gray-200 rounded px-2.5 py-1.5 flex items-center justify-between gap-1 w-full md:max-w-[140px] transition-colors">
          <span className="truncate">Phân loại: Mặc định</span>
          <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Unit Price Column */}
      <div className="w-full md:w-[12%] flex-shrink-0 text-left md:text-center flex md:flex-col justify-between md:justify-center items-center">
        <span className="md:hidden text-xs text-gray-400 font-medium">Đơn Giá:</span>
        <div className="flex flex-row md:flex-col items-center md:items-center gap-1.5">
          <span className="text-gray-400 line-through text-xs">{formatPrice(item.price * 1.15)}</span>
          <span className="text-gray-900 text-sm font-medium">{formatPrice(item.price)}</span>
        </div>
      </div>

      {/* Quantity Column */}
      <div className="w-full md:w-[12%] flex-shrink-0 flex md:justify-center items-center justify-between">
        <span className="md:hidden text-xs text-gray-400 font-medium">Số Lượng:</span>
        <div className="flex items-center border border-gray-300 rounded overflow-hidden h-8 bg-white shadow-sm">
          <button
            onClick={() => handleQuantityChange(item.quantity - 1)}
            disabled={item.quantity <= 1}
            className="w-7 h-full hover:bg-gray-100 disabled:opacity-40 flex items-center justify-center border-r border-gray-200 transition-colors"
          >
            <MinusIcon className="w-3 h-3 text-gray-600" />
          </button>
          <span className="w-9 text-center text-xs font-semibold text-gray-800">{item.quantity}</span>
          <button
            onClick={() => handleQuantityChange(item.quantity + 1)}
            className="w-7 h-full hover:bg-gray-100 flex items-center justify-center border-l border-gray-200 transition-colors"
          >
            <PlusIcon className="w-3 h-3 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Subtotal Column */}
      <div className="w-full md:w-[12%] flex-shrink-0 text-right md:text-center flex md:justify-center justify-between items-center">
        <span className="md:hidden text-xs text-gray-400 font-medium">Số Tiền:</span>
        <span className="font-semibold text-primary-600 text-sm">{formatPrice(item.subtotal)}</span>
      </div>

      {/* Actions Column */}
      <div className="w-full md:w-[8%] flex-shrink-0 text-right md:text-center flex md:flex-col justify-between md:justify-center items-end md:items-center gap-1">
        <span className="md:hidden text-xs text-gray-400 font-medium">Thao Tác:</span>
        <div className="flex md:flex-col items-center gap-2 md:gap-1">
          <button
            onClick={handleRemove}
            className="text-gray-600 hover:text-primary-600 text-xs font-medium transition-colors"
          >
            Xóa
          </button>
          <button className="hidden md:block text-[10px] text-primary-600 hover:underline transition-all">
            Tìm sản phẩm tương tự
          </button>
        </div>
      </div>
    </div>
  );
};

export default CartItem;
