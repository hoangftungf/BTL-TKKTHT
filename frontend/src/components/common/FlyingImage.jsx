import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const FlyingImage = ({ src, startRect, onComplete }) => {
  const [endRect, setEndRect] = useState(null);

  const getCartIconRect = useCallback(() => {
    const cartBtn = document.querySelector('.cart-icon-trigger');
    if (cartBtn) return cartBtn.getBoundingClientRect();
    return { left: window.innerWidth - 60, top: 60, width: 40, height: 40 };
  }, []);

  useEffect(() => {
    if (!startRect) return;
    // Small delay to let DOM settle
    const timer = setTimeout(() => {
      setEndRect(getCartIconRect());
    }, 50);
    return () => clearTimeout(timer);
  }, [startRect, getCartIconRect]);

  if (!startRect || !endRect) return null;

  const startX = startRect.left + startRect.width / 2 - 20;
  const startY = startRect.top + startRect.height / 2 - 20;
  const endX = endRect.left + endRect.width / 2 - 20;
  const endY = endRect.top + endRect.height / 2 - 20;

  return (
    <AnimatePresence>
      <motion.div
        initial={{
          position: 'fixed',
          left: startX,
          top: startY,
          width: 40,
          height: 40,
          zIndex: 9999,
          opacity: 1,
          scale: 1,
        }}
        animate={{
          left: endX,
          top: endY,
          width: 24,
          height: 24,
          opacity: 0.6,
          scale: 0.5,
        }}
        exit={{ opacity: 0, scale: 0.2 }}
        transition={{
          duration: 0.7,
          ease: [0.25, 0.1, 0.25, 1],
          opacity: { duration: 0.5 },
        }}
        onAnimationComplete={onComplete}
        style={{ pointerEvents: 'none' }}
      >
        <img
          src={src}
          alt=""
          className="w-full h-full object-contain rounded-full shadow-lg"
        />
      </motion.div>
    </AnimatePresence>
  );
};

export default FlyingImage;
