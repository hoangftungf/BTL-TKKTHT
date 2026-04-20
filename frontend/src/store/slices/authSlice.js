import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import authService from '../../services/authService';

const initialState = {
  user: null,
  tokens: JSON.parse(localStorage.getItem('tokens')) || null,
  isAuthenticated: !!localStorage.getItem('tokens'),
  loading: false,
  error: null,
};

export const login = createAsyncThunk('auth/login', async (credentials, { rejectWithValue }) => {
  try {
    const response = await authService.login(credentials);
    localStorage.setItem('tokens', JSON.stringify(response.tokens));
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data?.message || 'Đăng nhập thất bại');
  }
});

export const register = createAsyncThunk('auth/register', async (userData, { rejectWithValue }) => {
  try {
    const response = await authService.register(userData);
    localStorage.setItem('tokens', JSON.stringify(response.tokens));
    return response;
  } catch (error) {
    return rejectWithValue(error.response?.data || 'Đăng ký thất bại');
  }
});

export const logout = createAsyncThunk('auth/logout', async (_, { getState }) => {
  const { tokens } = getState().auth;
  if (tokens?.refresh) {
    try {
      await authService.logout(tokens.refresh);
    } catch (error) {
      console.error('Logout error:', error);
    }
  }
  localStorage.removeItem('tokens');
});

export const checkAuth = createAsyncThunk('auth/checkAuth', async (_, { getState, rejectWithValue }) => {
  const { tokens } = getState().auth;
  if (!tokens?.access) {
    return rejectWithValue('No token');
  }
  try {
    const user = await authService.getMe();
    return user;
  } catch (error) {
    localStorage.removeItem('tokens');
    return rejectWithValue('Token invalid');
  }
});

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.tokens = action.payload.tokens;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Register
      .addCase(register.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.tokens = action.payload.tokens;
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.tokens = null;
        state.isAuthenticated = false;
      })
      // Check Auth
      .addCase(checkAuth.fulfilled, (state, action) => {
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(checkAuth.rejected, (state) => {
        state.user = null;
        state.tokens = null;
        state.isAuthenticated = false;
      });
  },
});

export const { clearError } = authSlice.actions;
export default authSlice.reducer;
