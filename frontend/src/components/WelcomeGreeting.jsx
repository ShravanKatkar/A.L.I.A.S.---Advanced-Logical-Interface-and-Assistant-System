import React from 'react'
import { motion, useReducedMotion } from 'framer-motion'

/**
 * WelcomeGreeting
 * 
 * Minimalist, stationary welcome greeting for A.L.I.A.S.
 * - Modest font size (small, not bold).
 * - Pure stationary fade transition (zero sliding / position movement).
 * - Smooth opacity & soft focus dissolve.
 * - Completely still once settled.
 * - Respects prefers-reduced-motion.
 */
export default function WelcomeGreeting({ name = '' }) {
  const shouldReduceMotion = useReducedMotion()
  const displayName = name ? name.trim() : ''

  // Words list for staggered fade transition
  const words = displayName
    ? [`${displayName},`, 'how', 'can', 'I', 'assist', 'you?']
    : ['How', 'can', 'I', 'assist', 'you?']

  // Reduced motion fallback
  if (shouldReduceMotion) {
    return (
      <div className="select-none text-center px-4 max-w-2xl mx-auto flex flex-col items-center justify-center">
        <h1 className="text-xl sm:text-2xl md:text-[25px] font-normal tracking-[-0.015em] text-gray-900 dark:text-neutral-100">
          {displayName ? `${displayName}, how can I assist you?` : 'How can I assist you?'}
        </h1>
      </div>
    )
  }

  // Pure fade & focus dissolve variants (zero sliding / no y-axis displacement)
  const wordVariants = {
    initial: {
      opacity: 0,
      filter: 'blur(4px)'
    },
    animate: (i) => ({
      opacity: 1,
      filter: 'blur(0px)',
      transition: {
        duration: 0.45,
        delay: i * 0.05,
        ease: 'easeOut'
      }
    })
  }

  return (
    <div className="relative select-none text-center px-4 max-w-2xl mx-auto flex flex-col items-center justify-center pointer-events-none">
      <h1 className="text-xl sm:text-2xl md:text-[25px] font-normal tracking-[-0.015em] leading-relaxed text-gray-900 dark:text-neutral-100 flex flex-wrap items-center justify-center">
        {words.map((word, index) => (
          <span
            key={`${word}-${index}`}
            className="inline-block py-0.5 mr-[0.28em] last:mr-0"
          >
            <motion.span
              custom={index}
              variants={wordVariants}
              initial="initial"
              animate="animate"
              className="inline-block font-normal text-gray-900 dark:text-neutral-100"
            >
              {word}
            </motion.span>
          </span>
        ))}
      </h1>
    </div>
  )
}
