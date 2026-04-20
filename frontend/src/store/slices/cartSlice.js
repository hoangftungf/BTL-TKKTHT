import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import cartService from '../../services/cartService';

const initialState = {
  items: [],
  totalItems: 0,
  totalAmount: 0,
  loading: false,
  error: null,
};

export const fetchCart = createAsyncThunk('cart/fetchCart', async (_, { rejectWithValue }) => {
  try {
    const response = await cartService.getCart();
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Lỗi tải giỏ hàng');
  }
});

export const addToCart = createAsyncThunk('cart/addToCart', async ({ productId, quantity = 1 }, { rejectWithValue }) => {
  try {
    const response = await cartService.addItem(productId, quantity);
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Lỗi thêm vào giỏ');
  }
});

export const updateCartItem = createAsyncThunk('cart/updateCartItem', async ({ itemId, quantity }, { rejectWithValue }) => {
  try {
    const response = await cartService.updateItem(itemId, quantity);
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Lỗi cập nhật');
  }
});

export const removeCartItem = createAsyncThunk('cart/removeCartItem', async (itemId, { rejectWithValue }) => {
  try {
    await cartService.removeItem(itemId);
    return itemId;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Lỗi xóa sản phẩm');
  }
});

export const clearCart = createAsyncThunk('cart/clearCart', async (_, { rejectWithValue }) => {
  try {
    await cartService.clearCart();
    return true;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Lỗi xóa giỏ hàng');
  }
});

const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    resetCart: (state) => {
      state.items = [];
      state.totalItems = 0;
      state.totalAmount = 0;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCart.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchCart.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload.items || [];
        state.totalItems = action.payload.total_items || 0;
        state.totalAmount = action.payload.total_amount || 0;
      })
      .addCase(fetchCart.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(addToCart.fulfilled, (state, action) => {
        const existingItem = state.items.find(item => item.id === action.payload.id);
        if (existingItem) {
          existingItem.quantity = action.payload.quantity;
        } else {
          state.items.push(action.payload);
        }
        state.totalItems = state.items.reduce((sum, item) => sum + item.quantity, 0);
        state.totalAmount = state.items.reduce((sum, item) => sum + item.subtotal, 0);
      })
      .addCase(updateCartItem.fulfilled, (state, action) => {
        const item = state.items.find(item => item.id === action.payload.id);
        if (item) {
          item.quantity = action.payload.quantity;
          item.subtotal = action.payload.subtotal;
        }
        state.totalItems = state.items.reduce((sum, item) => sum + item.quantity, 0);
        state.totalAmount = state.items.reduce((sum, item) => sum + item.subtotal, 0);
      })
      .addCase(removeCartItem.fulfilled, (state, action) => {
        state.items = state.items.filter(item => item.id !== action.payload);
        state.totalItems = state.items.reduce((sum, item) => sum + item.quantity, 0);
        state.totalAmount = state.items.reduce((sum, item) => sum + item.subtotal, 0);
      })
      .addCase(clearCart.fulfilled, (state) => {
        state.items = [];
        state.totalItems = 0;
        state.totalAmount = 0;
      });
  },
});

export const { resetCart } = cartSlice.actions;
export default cartSlice.reducer;
