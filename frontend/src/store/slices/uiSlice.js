import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  sidebarOpen: false,
  cartDrawerOpen: false,
  searchModalOpen: false,
  mobileMenuOpen: false,
  loginModalOpen: false,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action) => {
      state.sidebarOpen = action.payload;
    },
    toggleCartDrawer: (state) => {
      state.cartDrawerOpen = !state.cartDrawerOpen;
    },
    setCartDrawerOpen: (state, action) => {
      state.cartDrawerOpen = action.payload;
    },
    toggleSearchModal: (state) => {
      state.searchModalOpen = !state.searchModalOpen;
    },
    setSearchModalOpen: (state, action) => {
      state.searchModalOpen = action.payload;
    },
    toggleMobileMenu: (state) => {
      state.mobileMenuOpen = !state.mobileMenuOpen;
    },
    setMobileMenuOpen: (state, action) => {
      state.mobileMenuOpen = action.payload;
    },
    toggleLoginModal: (state) => {
      state.loginModalOpen = !state.loginModalOpen;
    },
    setLoginModalOpen: (state, action) => {
      state.loginModalOpen = action.payload;
    },
  },
});

export const {
  toggleSidebar,
  setSidebarOpen,
  toggleCartDrawer,
  setCartDrawerOpen,
  toggleSearchModal,
  setSearchModalOpen,
  toggleMobileMenu,
  setMobileMenuOpen,
  toggleLoginModal,
  setLoginModalOpen,
} = uiSlice.actions;

export default uiSlice.reducer;
