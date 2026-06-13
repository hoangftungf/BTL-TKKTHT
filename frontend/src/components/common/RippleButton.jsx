import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const RippleButton = ({
  children,
  onClick,
  className = '',
  disabled = false,
  type = 'button',
  rippleColor = 'rgba(255,255,255,0.4)',
  ...props
}) => {
  const [ripples, setRipples] = useState([]);

  const handleClick = useCallback(
    (e) => {
      if (disabled) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const size = Math.max(rect.width, rect.height) * 2;

      const id = Date.now() + Math.random();
      setRipples((prev) => [...prev, { id, x, y, size }]);

      onClick?.(e);
    },
    [disabled, onClick]
  );

  const removeRipple = (id) => {
    setRipples((prev) => prev.filter((r) => r.id !== id));
  };

  return (
    <button
      type={type}
      onClick={handleClick}
      disabled={disabled}
      className={`relative overflow-hidden ${className}`}
      style={{ WebkitTapHighlightColor: 'transparent' }}
      {...props}
    >
      {children}
      <AnimatePresence>
        {ripples.map((ripple) => (
          <motion.span
            key={ripple.id}
            initial={{ scale: 0, opacity: 0.6, x: ripple.x - ripple.size / 2, y: ripple.y - ripple.size / 2 }}
            animate={{ scale: 1, opacity: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            onAnimationComplete={() => removeRipple(ripple.id)}
            style={{
              position: 'absolute',
              borderRadius: '50%',
              width: ripple.size,
              height: ripple.size,
              backgroundColor: rippleColor,
              pointerEvents: 'none',
            }}
          />
        ))}
      </AnimatePresence>
    </button>
  );
};

export default RippleButton;
