import { Variants } from 'framer-motion';

// ===== FADE VARIANTS =====
export const fadeIn = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.3 } },
  exit: { opacity: 0, transition: { duration: 0.2 } },
};

export const fadeInUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } },
  exit: { opacity: 0, y: -12, transition: { duration: 0.2 } },
};

export const fadeInDown = {
  hidden: { opacity: 0, y: -16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' } },
  exit: { opacity: 0, y: -16, transition: { duration: 0.2 } },
};

export const fadeInLeft = {
  hidden: { opacity: 0, x: -24 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.35, ease: 'easeOut' } },
  exit: { opacity: 0, x: -24, transition: { duration: 0.2 } },
};

export const fadeInRight = {
  hidden: { opacity: 0, x: 24 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.35, ease: 'easeOut' } },
  exit: { opacity: 0, x: 24, transition: { duration: 0.2 } },
};

// ===== SCALE VARIANTS =====
export const scaleIn = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.3, ease: 'easeOut' } },
  exit: { opacity: 0, scale: 0.9, transition: { duration: 0.2 } },
};

export const scaleInBounce = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { opacity: 1, scale: 1, transition: { type: 'spring', stiffness: 400, damping: 15 } },
  exit: { opacity: 0, scale: 0.8, transition: { duration: 0.15 } },
};

// ===== STAGGER VARIANTS =====
export const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06,
      delayChildren: 0.1,
      ease: 'easeOut',
    },
  },
  exit: { opacity: 0, transition: { duration: 0.15 } },
};

export const staggerItem = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: 'easeOut' },
  },
  exit: { opacity: 0, y: -10, transition: { duration: 0.2 } },
};

// ===== SLIDE VARIANTS =====
export const slideInLeft = {
  hidden: { x: '-100%' },
  visible: { x: 0, transition: { type: 'spring', stiffness: 300, damping: 30 } },
  exit: { x: '-100%', transition: { duration: 0.2 } },
};

export const slideInRight = {
  hidden: { x: '100%' },
  visible: { x: 0, transition: { type: 'spring', stiffness: 300, damping: 30 } },
  exit: { x: '100%', transition: { duration: 0.2 } },
};

// ===== POP / BOUNCE =====
export const popIn = {
  hidden: { opacity: 0, scale: 0.5 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { type: 'spring', stiffness: 500, damping: 12 },
  },
};

export const badgeBounce = {
  initial: { scale: 0 },
  animate: { scale: 1, transition: { type: 'spring', stiffness: 600, damping: 10 } },
};

// ===== SHIMMER =====
export const shimmer = {
  animate: {
    backgroundPosition: ['200% 0', '-200% 0'],
    transition: { repeat: Infinity, duration: 1.5, ease: 'linear' },
  },
};

// ===== SHAKE =====
export const shake = {
  animate: {
    x: [0, -10, 10, -10, 10, -5, 5, -2, 2, 0],
    transition: { duration: 0.5, ease: 'easeInOut' },
  },
};

// ===== DRAW / CHECKMARK =====
export const drawCheck = {
  hidden: { pathLength: 0, opacity: 0 },
  visible: {
    pathLength: 1,
    opacity: 1,
    transition: { duration: 0.5, ease: 'easeInOut' },
  },
};

// ===== PARALLAX =====
export const parallaxSection = (scrollYProgress, speed = 0.3) => ({
  y: scrollYProgress.current * speed * 100,
});

// ===== COUNT UP =====
export const countUp = (end, duration = 1.5) => ({
  hidden: { count: 0 },
  visible: { count: end, transition: { duration, ease: 'easeOut' } },
});

// ===== CARD HOVER =====
export const cardHover = {
  rest: { scale: 1, y: 0 },
  hover: {
    scale: 1.02,
    y: -4,
    transition: { type: 'spring', stiffness: 300, damping: 15 },
  },
  tap: { scale: 0.98 },
};

// ===== BUTTON TAP =====
export const buttonTap = {
  rest: { scale: 1 },
  tap: { scale: 0.95 },
};
