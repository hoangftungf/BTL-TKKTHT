import { motion } from 'framer-motion';

const ShimmerText = ({
  children,
  className = '',
  colors = ['#6366f1', '#ec4899', '#6366f1'],
  duration = 3,
}) => {
  const gradientColors = colors.join(', ');

  return (
    <motion.span
      className={`inline-block bg-clip-text text-transparent font-bold ${className}`}
      style={{
        backgroundImage: `linear-gradient(90deg, ${gradientColors}, ${colors[0]})`,
        backgroundSize: '200% 100%',
      }}
      animate={{
        backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
      }}
      transition={{
        duration,
        repeat: Infinity,
        ease: 'linear',
      }}
    >
      {children}
    </motion.span>
  );
};

export default ShimmerText;
