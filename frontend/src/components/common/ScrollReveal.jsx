import { motion } from 'framer-motion';

const variantsMap = {
  up: { hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0 } },
  down: { hidden: { opacity: 0, y: -40 }, visible: { opacity: 1, y: 0 } },
  left: { hidden: { opacity: 0, x: -40 }, visible: { opacity: 1, x: 0 } },
  right: { hidden: { opacity: 0, x: 40 }, visible: { opacity: 1, x: 0 } },
  scale: { hidden: { opacity: 0, scale: 0.85 }, visible: { opacity: 1, scale: 1 } },
  none: { hidden: { opacity: 0 }, visible: { opacity: 1 } },
};

const ScrollReveal = ({
  children,
  direction = 'up',
  delay = 0,
  duration = 0.5,
  once = true,
  distance = 40,
  className = '',
  style = {},
}) => {
  const base = variantsMap[direction] || variantsMap.up;
  const hidden = { ...base.hidden };
  if (direction === 'up' || direction === 'down') hidden.y = distance * (direction === 'up' ? 1 : -1);
  if (direction === 'left' || direction === 'right') hidden.x = distance * (direction === 'left' ? 1 : -1);

  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once, margin: '-50px' }}
      variants={{
        hidden,
        visible: {
          ...base.visible,
          transition: { duration, delay, ease: 'easeOut' },
        },
      }}
      className={className}
      style={style}
    >
      {children}
    </motion.div>
  );
};

export default ScrollReveal;
