import { motion } from 'framer-motion';

const Loading = ({ size = 'md', text = 'Đang tải...', variant = 'spinner' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  if (variant === 'shimmer') {
    return (
      <div className="space-y-4 w-full">
        <motion.div
          className="h-4 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 rounded"
          animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}
          transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}
          style={{ backgroundSize: '200% 100%' }}
        />
        <motion.div
          className="h-4 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 rounded w-3/4"
          animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}
          transition={{ repeat: Infinity, duration: 1.5, ease: 'linear', delay: 0.1 }}
          style={{ backgroundSize: '200% 100%' }}
        />
        <motion.div
          className="h-4 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 rounded w-1/2"
          animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}
          transition={{ repeat: Infinity, duration: 1.5, ease: 'linear', delay: 0.2 }}
          style={{ backgroundSize: '200% 100%' }}
        />
      </div>
    );
  }

  if (variant === 'skeleton') {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <motion.div
          className={`${sizeClasses[size]} border-4 border-primary-200 border-t-primary-600 rounded-full`}
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
        />
        {text && (
          <motion.p
            className="mt-4 text-gray-500"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            {text}
          </motion.p>
        )}
      </div>
    );
  }

  // Default spinner
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <motion.div
        className={`${sizeClasses[size]} border-4 border-primary-200 border-t-primary-600 rounded-full`}
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
      />
      {text && (
        <motion.p
          className="mt-4 text-gray-500"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          {text}
        </motion.p>
      )}
    </div>
  );
};

export default Loading;
