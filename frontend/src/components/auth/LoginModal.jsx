import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { login, clearError } from '../../store/slices/authSlice';
import { setLoginModalOpen } from '../../store/slices/uiSlice';
import { XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const LoginModal = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const dispatch = useDispatch();

  const { isAuthenticated, loading, error } = useSelector((state) => state.auth);
  const { loginModalOpen } = useSelector((state) => state.ui);

  useEffect(() => {
    if (isAuthenticated && loginModalOpen) {
      dispatch(setLoginModalOpen(false));
      toast.success('Đăng nhập thành công!');
      setEmail('');
      setPassword('');
    }
  }, [isAuthenticated, loginModalOpen, dispatch]);

  useEffect(() => {
    if (error) {
      toast.error(error);
      dispatch(clearError());
    }
  }, [error, dispatch]);

  const handleClose = () => {
    dispatch(setLoginModalOpen(false));
    setEmail('');
    setPassword('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(login({ email, password }));
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      handleClose();
    }
  };

  if (!loginModalOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black bg-opacity-50"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 relative animate-fade-in">
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-1 text-gray-400 hover:text-gray-600"
        >
          <XMarkIcon className="w-6 h-6" />
        </button>

        <div className="p-8">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Đăng nhập</h2>
            <p className="text-gray-500 mt-2">Vui lòng đăng nhập để tiếp tục</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="your@email.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
                required
              />
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Chưa có tài khoản?{' '}
              <Link
                to="/register"
                onClick={handleClose}
                className="text-primary-600 hover:underline font-medium"
              >
                Đăng ký ngay
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginModal;
