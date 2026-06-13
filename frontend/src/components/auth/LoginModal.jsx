import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import { login, clearError } from '../../store/slices/authSlice';
import { setLoginModalOpen } from '../../store/slices/uiSlice';
import { XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const modalVariants = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { type: 'spring', stiffness: 300, damping: 25 },
  },
  shake: {
    x: [0, -10, 10, -10, 10, -5, 5, -2, 2, 0],
    transition: { duration: 0.5, ease: 'easeInOut' },
  },
  exit: { opacity: 0, scale: 0.9, transition: { duration: 0.2 } },
};

const LoginModal = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [animateState, setAnimateState] = useState('visible');
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
      let errorMsg = 'Đăng nhập thất bại';
      if (typeof error === 'string') {
        errorMsg = error;
      } else if (typeof error === 'object') {
        const messages = [];
        Object.values(error).forEach(val => {
          if (Array.isArray(val)) {
            messages.push(...val.map(v => String(v)));
          } else if (val) {
            messages.push(String(val));
          }
        });
        if (messages.length > 0) {
          errorMsg = messages.join(', ');
        }
      }
      toast.error(errorMsg);
      setAnimateState('shake');
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

  return (
    <AnimatePresence>
      {loginModalOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black bg-opacity-50"
          onClick={handleBackdropClick}
        >
          <motion.div
            variants={modalVariants}
            initial="hidden"
            animate={animateState}
            exit="exit"
            onAnimationComplete={() => animateState === 'shake' && setAnimateState('visible')}
            className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 relative"
          >
            <motion.button
              onClick={handleClose}
              className="absolute top-4 right-4 p-1 text-gray-400 hover:text-gray-600"
              whileHover={{ rotate: 90, scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <XMarkIcon className="w-6 h-6" />
            </motion.button>

            <div className="p-8">
              <motion.div
                className="text-center mb-6"
                initial={{ y: -10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.1 }}
              >
                <h2 className="text-2xl font-bold text-gray-900">Đăng nhập</h2>
                <p className="text-gray-500 mt-2">Vui lòng đăng nhập để tiếp tục</p>
              </motion.div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <motion.div
                  initial={{ x: -10, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.15 }}
                >
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="input"
                    placeholder="your@email.com"
                    required
                  />
                </motion.div>

                <motion.div
                  initial={{ x: -10, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  <label className="block text-sm font-medium text-gray-700 mb-1">Mật khẩu</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input"
                    placeholder="••••••••"
                    required
                  />
                </motion.div>

                <motion.button
                  type="submit"
                  disabled={loading}
                  className="btn-primary w-full"
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.25 }}
                >
                  {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
                </motion.button>
              </form>

              <motion.div
                className="mt-6 text-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
              >
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
              </motion.div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default LoginModal;
