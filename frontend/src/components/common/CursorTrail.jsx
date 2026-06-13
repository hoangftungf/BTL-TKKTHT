import { useEffect, useRef, useCallback } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

const CursorTrail = ({ color = '#6366f1', size = 6, trailLength = 8 }) => {
  const cursorX = useMotionValue(-100);
  const cursorY = useMotionValue(-100);
  const springConfig = { damping: 25, stiffness: 200, mass: 0.5 };
  const springX = useSpring(cursorX, springConfig);
  const springY = useSpring(cursorY, springConfig);
  const trailRefs = useRef([]);

  const handleMouseMove = useCallback(
    (e) => {
      cursorX.set(e.clientX - size / 2);
      cursorY.set(e.clientY - size / 2);
    },
    [cursorX, cursorY, size]
  );

  useEffect(() => {
    const isDesktop = window.matchMedia('(pointer: fine)').matches;
    if (!isDesktop) return;

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [handleMouseMove]);

  return (
    <>
      {Array.from({ length: trailLength }).map((_, i) => {
        const scale = 1 - i / trailLength;
        const opacity = 0.4 - i * 0.05;
        return (
          <motion.div
            key={i}
            className="pointer-events-none fixed z-[9999] rounded-full"
            style={{
              width: size * scale,
              height: size * scale,
              backgroundColor: color,
              opacity: Math.max(0, opacity),
              x: springX,
              y: springY,
            }}
          />
        );
      })}
    </>
  );
};

export default CursorTrail;
