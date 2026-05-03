import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import userService from '../../services/userService';
import { logout } from './authSlice';

const initialState = {
  items: [],
  productIds: [], // Quick lookup set
  loading: false,
  error: null,
};

export const fetchWishlist = createAsyncThunk('wishlist/fetchWishlist', async (_, { rejectWithValue }) => {
  try {
    const response = await userService.getWishlist();
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Loi tai danh sach yeu thich');
  }
});

export const addToWishlist = createAsyncThunk('wishlist/addToWishlist', async (productId, { rejectWithValue }) => {
  try {
    await userService.addToWishlist(productId);
    return productId;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Loi them vao yeu thich');
  }
});

export const removeFromWishlist = createAsyncThunk('wishlist/removeFromWishlist', async (productId, { rejectWithValue }) => {
  try {
    await userService.removeFromWishlist(productId);
    return productId;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Loi xoa khoi yeu thich');
  }
});

const wishlistSlice = createSlice({
  name: 'wishlist',
  initialState,
  reducers: {
    resetWishlist: (state) => {
      state.items = [];
      state.productIds = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchWishlist.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchWishlist.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload || [];
        state.productIds = (action.payload || []).map(item => item.product_id);
      })
      .addCase(fetchWishlist.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(addToWishlist.fulfilled, (state, action) => {
        if (!state.productIds.includes(action.payload)) {
          state.productIds.push(action.payload);
          state.items.push({ product_id: action.payload });
        }
      })
      .addCase(removeFromWishlist.fulfilled, (state, action) => {
        state.productIds = state.productIds.filter(id => id !== action.payload);
        state.items = state.items.filter(item => item.product_id !== action.payload);
      })
      // Reset on logout
      .addCase(logout.fulfilled, (state) => {
        state.items = [];
        state.productIds = [];
        state.loading = false;
        state.error = null;
      });
  },
});

export const { resetWishlist } = wishlistSlice.actions;
export default wishlistSlice.reducer;
