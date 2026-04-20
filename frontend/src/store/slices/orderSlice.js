import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import orderService from '../../services/orderService';

const initialState = {
  orders: [],
  currentOrder: null,
  loading: false,
  error: null,
};

export const fetchOrders = createAsyncThunk('order/fetchOrders', async (_, { rejectWithValue }) => {
  try {
    const response = await orderService.getOrders();
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Lỗi tải đơn hàng');
  }
});

export const fetchOrderById = createAsyncThunk('order/fetchOrderById', async (id, { rejectWithValue }) => {
  try {
    const response = await orderService.getOrderById(id);
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Không tìm thấy đơn hàng');
  }
});

export const createOrder = createAsyncThunk('order/createOrder', async (orderData, { rejectWithValue }) => {
  try {
    const response = await orderService.createOrder(orderData);
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Lỗi tạo đơn hàng');
  }
});

export const cancelOrder = createAsyncThunk('order/cancelOrder', async ({ orderId, reason }, { rejectWithValue }) => {
  try {
    const response = await orderService.cancelOrder(orderId, reason);
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Lỗi hủy đơn hàng');
  }
});

const orderSlice = createSlice({
  name: 'order',
  initialState,
  reducers: {
    clearCurrentOrder: (state) => {
      state.currentOrder = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchOrders.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchOrders.fulfilled, (state, action) => {
        state.loading = false;
        state.orders = action.payload;
      })
      .addCase(fetchOrders.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(fetchOrderById.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchOrderById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentOrder = action.payload;
      })
      .addCase(fetchOrderById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(createOrder.pending, (state) => {
        state.loading = true;
      })
      .addCase(createOrder.fulfilled, (state, action) => {
        state.loading = false;
        state.currentOrder = action.payload;
        state.orders.unshift(action.payload);
      })
      .addCase(createOrder.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(cancelOrder.fulfilled, (state, action) => {
        const index = state.orders.findIndex(o => o.id === action.payload.id);
        if (index !== -1) {
          state.orders[index] = action.payload;
        }
        if (state.currentOrder?.id === action.payload.id) {
          state.currentOrder = action.payload;
        }
      });
  },
});

export const { clearCurrentOrder } = orderSlice.actions;
export default orderSlice.reducer;
