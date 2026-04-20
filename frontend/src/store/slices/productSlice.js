import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import productService from '../../services/productService';

const initialState = {
  products: [],
  featuredProducts: [],
  currentProduct: null,
  categories: [],
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },
  filters: {
    category: null,
    minPrice: null,
    maxPrice: null,
    brand: null,
    ordering: '-created_at',
  },
  loading: false,
  error: null,
};

export const fetchProducts = createAsyncThunk('product/fetchProducts', async (params, { rejectWithValue }) => {
  try {
    const response = await productService.getProducts(params);
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Lỗi tải sản phẩm');
  }
});

export const fetchProductById = createAsyncThunk('product/fetchProductById', async (id, { rejectWithValue }) => {
  try {
    const response = await productService.getProductById(id);
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Không tìm thấy sản phẩm');
  }
});

export const fetchCategories = createAsyncThunk('product/fetchCategories', async (_, { rejectWithValue }) => {
  try {
    const response = await productService.getCategories();
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Lỗi tải danh mục');
  }
});

export const searchProducts = createAsyncThunk('product/searchProducts', async (query, { rejectWithValue }) => {
  try {
    const response = await productService.searchProducts(query);
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Lỗi tìm kiếm');
  }
});

export const fetchFeaturedProducts = createAsyncThunk('product/fetchFeaturedProducts', async (_, { rejectWithValue }) => {
  try {
    const response = await productService.getProducts({ is_featured: true, page_size: 8 });
    return response.results;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Lỗi tải sản phẩm nổi bật');
  }
});

const productSlice = createSlice({
  name: 'product',
  initialState,
  reducers: {
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = initialState.filters;
    },
    clearCurrentProduct: (state) => {
      state.currentProduct = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch Products
      .addCase(fetchProducts.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.loading = false;
        state.products = action.payload.results;
        state.pagination = {
          page: action.payload.page,
          pageSize: action.payload.page_size,
          total: action.payload.count,
        };
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Fetch Product by ID
      .addCase(fetchProductById.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchProductById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentProduct = action.payload;
      })
      .addCase(fetchProductById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Categories
      .addCase(fetchCategories.fulfilled, (state, action) => {
        state.categories = action.payload;
      })
      // Search
      .addCase(searchProducts.pending, (state) => {
        state.loading = true;
      })
      .addCase(searchProducts.fulfilled, (state, action) => {
        state.loading = false;
        state.products = action.payload.results;
      })
      .addCase(searchProducts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Featured
      .addCase(fetchFeaturedProducts.fulfilled, (state, action) => {
        state.featuredProducts = action.payload;
      });
  },
});

export const { setFilters, clearFilters, clearCurrentProduct } = productSlice.actions;
export default productSlice.reducer;
