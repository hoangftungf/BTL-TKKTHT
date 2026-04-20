import { useDispatch } from 'react-redux';
import { updateCartItem, removeCartItem } from '../../store/slices/cartSlice';
import { TrashIcon, MinusIcon, PlusIcon } from '@heroicons/react/24/outline';
import { formatPrice } from '../../utils/format';
import toast from 'react-hot-toast';

const CartItem = ({ item }) => {
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
    <div className="flex items-start space-x-4 py-4 border-b border-gray-100 last:border-0">
      {/* Image */}
      <div className="w-20 h-20 flex-shrink-0 rounded-lg overflow-hidden bg-gray-100">
        <img
          src={item.product_image || '/placeholder.png'}
          alt={item.product_name}
          className="w-full h-full object-cover"
        />
      </div>

      {/* Info */}
      <div className="flex-grow min-w-0">
        <h4 className="font-medium text-gray-900 truncate">{item.product_name}</h4>
        <p className="text-red-600 font-semibold mt-1">{formatPrice(item.price)}</p>

        {/* Quantity Controls */}
        <div className="flex items-center space-x-2 mt-2">
          <button
            onClick={() => handleQuantityChange(item.quantity - 1)}
            disabled={item.quantity <= 1}
            className="p-1 rounded border border-gray-300 hover:bg-gray-100 disabled:opacity-50"
          >
            <MinusIcon className="w-4 h-4" />
          </button>
          <span className="w-10 text-center font-medium">{item.quantity}</span>
          <button
            onClick={() => handleQuantityChange(item.quantity + 1)}
            className="p-1 rounded border border-gray-300 hover:bg-gray-100"
          >
            <PlusIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Subtotal & Remove */}
      <div className="text-right flex-shrink-0">
        <p className="font-semibold text-gray-900">{formatPrice(item.subtotal)}</p>
        <button
          onClick={handleRemove}
          className="mt-2 p-1 text-gray-400 hover:text-red-500"
        >
          <TrashIcon className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

export default CartItem;
