import { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';

const ParallaxSection = ({
  children,
  bgImage,
  speed = 0.3,
  className = '',
  overlay = true,
  overlayColor = 'rgba(0,0,0,0.3)',
}) => {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start end', 'end start'],
  });

  const y = useTransform(scrollYProgress, [0, 1], [speed * 200, speed * -200]);
  const opacity = useTransform(scrollYProgress, [0, 0.3, 0.7, 1], [0.6, 1, 1, 0.6]);

  return (
    <div ref={ref} className={`relative overflow-hidden ${className}`}>
      <motion.div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage: bgImage ? `url(${bgImage})` : undefined,
          y,
        }}
      />
      {overlay && (
        <div
          className="absolute inset-0"
          style={{ backgroundColor: overlayColor }}
        />
      )}
      <motion.div className="relative z-10" style={{ opacity }}>
        {children}
      </motion.div>
    </div>
  );
};

export default ParallaxSection;
