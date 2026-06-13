import { motion } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { fadeInUp } from '../../utils/animations';

const PageTransition = ({ children, className = '' }) => {
  const location = useLocation();

  return (
    <motion.div
      key={location.pathname}
      variants={fadeInUp}
      initial="hidden"
      animate="visible"
      exit="exit"
      className={className}
    >
      {children}
    </motion.div>
  );
};

export default PageTransition;
