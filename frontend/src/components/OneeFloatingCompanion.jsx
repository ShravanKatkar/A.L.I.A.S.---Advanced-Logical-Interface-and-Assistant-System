import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, VolumeX, Sparkles, ChevronDown, ChevronUp, MessageCircle, X } from 'lucide-react'
import { Avatar } from '@bible-strong/avatar-react'
import defaultAlienDef from '../assets/alien-avatar-definition.json'

/**
 * OneeFloatingCompanion
 * 
 * Recreates the authentic glowing animated AI desktop companion from the reference screenshot:
 * - Neon lime-green alien companion with organic round body and top antenna
 * - Transparent surroundings (no rectangular card or panel wrapper)
 * - Soft outer neon glow with bloom
 * - Smooth floating vertical animation (gentle bobbing motion)
 * - Dynamic white thought/speech bubble connected via cascading circular tail dots
 * - Real-time state connection: Idle, Listening, Thinking, Speaking, Happy, Confused
 */
export default function OneeFloatingCompanion({
  definition = defaultAlienDef,
  animation = 'idle',
  expression = null,
  isListening = false,
  speechText = '',
  size = 78,
  onToggleVoice = null,
  onStopTTS = null,
  onTriggerReaction = null,
  positionMode = 'docked', // 'docked' (alongside text box) or 'floating' (bottom-right corner)
  showSpeechBubble = true,
  enableGlow = true,
  className = ''
}) {
  const [isMinimized, setIsMinimized] = useState(false)
  const [pokeMessage, setPokeMessage] = useState('')
  const [customAnimation, setCustomAnimation] = useState(null)
  const [isHovered, setIsHovered] = useState(false)
  const [bubbleDismissed, setBubbleDismissed] = useState(false)
  const pokeTimeoutRef = useRef(null)

  // Fun playful responses when clicked or poked
  const pokeReactions = [
    { anim: 'playful', text: 'Ready whenever you are!' },
    { anim: 'curious', text: 'What are we working on next?' },
    { anim: 'laughing', text: 'Hehe! At your service.' },
    { anim: 'excited', text: 'Let\'s create something awesome!' },
    { anim: 'proud', text: 'Your intelligent desktop companion.' },
    { anim: 'shy', text: 'Always here to assist you!' },
  ]

  const handlePoke = () => {
    const random = pokeReactions[Math.floor(Math.random() * pokeReactions.length)]
    setCustomAnimation(random.anim)
    setPokeMessage(random.text)
    setBubbleDismissed(false)

    if (onTriggerReaction) {
      onTriggerReaction(random.anim)
    }

    if (pokeTimeoutRef.current) clearTimeout(pokeTimeoutRef.current)
    pokeTimeoutRef.current = setTimeout(() => {
      setCustomAnimation(null)
      setPokeMessage('')
    }, 4500)
  }

  // Active animation to display
  const activeAnim = customAnimation || animation || 'idle'

  // Determine dynamic speech bubble text
  const getBubbleContent = () => {
    // 1. Interactive poke message has highest transient priority
    if (pokeMessage) return pokeMessage

    // 2. Real assistant response or streaming speech
    if (speechText && speechText.trim()) {
      return speechText.trim()
    }

    // 3. Dynamic assistant states & expressions
    if (isListening || activeAnim === 'listening') {
      return "I'm listening..."
    }
    if (activeAnim === 'thinking' || expression === 'curious-left') {
      return "Let me think..."
    }
    if (activeAnim === 'working' || expression === 'attentive-left') {
      return "Focusing on this..."
    }
    if (activeAnim === 'celebrate' || expression === 'joyful-wide') {
      return "All done! Glad to help."
    }
    if (activeAnim === 'confused' || expression === 'surprised-left') {
      return "Oops! Let's check that."
    }
    if (expression === 'playful-right' || activeAnim === 'happy') {
      return "Here you go! ✨"
    }
    if (expression === 'skeptical-left') {
      return "Hmm, analyzing carefully..."
    }
    if (expression === 'shy-downward') {
      return "Thank you so much!"
    }
    if (activeAnim === 'sleeping' || expression === 'sleepy-squint') {
      return "zZz..."
    }

    // 4. Subtle idle greeting
    return "Hi, I'm ALIAS! How can I assist you?"
  }

  const currentBubbleText = getBubbleContent()

  // Format and shorten display text for the thought bubble if too long
  const displayBubbleText = currentBubbleText.length > 140 
    ? currentBubbleText.slice(0, 137) + '...' 
    : currentBubbleText

  // Dynamic glow effect matching avatar color (defaults to neon lime green)
  const getAvatarGlowStyle = () => {
    if (!enableGlow) return {}
    const bodyColor = definition?.colors?.body?.toLowerCase() || '#84cc16'
    if (bodyColor.includes('84cc16') || bodyColor.includes('8cf81e') || bodyColor.includes('a3e635') || bodyColor.includes('green')) {
      return {
        filter: 'drop-shadow(0 0 14px rgba(132, 204, 22, 0.65)) drop-shadow(0 0 28px rgba(163, 230, 53, 0.3))'
      }
    }
    if (bodyColor.includes('3b82f6') || bodyColor.includes('60a5fa') || bodyColor.includes('blue')) {
      return {
        filter: 'drop-shadow(0 0 14px rgba(59, 130, 246, 0.6)) drop-shadow(0 0 28px rgba(96, 165, 250, 0.3))'
      }
    }
    if (bodyColor.includes('f59e0b') || bodyColor.includes('amber') || bodyColor.includes('yellow')) {
      return {
        filter: 'drop-shadow(0 0 14px rgba(245, 158, 11, 0.6)) drop-shadow(0 0 28px rgba(251, 191, 36, 0.3))'
      }
    }
    return {
      filter: 'drop-shadow(0 0 14px rgba(132, 204, 22, 0.65)) drop-shadow(0 0 28px rgba(163, 230, 53, 0.3))'
    }
  }

  // Floating bob animation variants
  const floatingVariants = {
    float: {
      y: positionMode === 'docked' ? [0, -3, 0] : [0, -7, 0],
      rotate: [0, 0.8, -0.8, 0],
      transition: {
        duration: 3.2,
        repeat: Infinity,
        ease: 'easeInOut'
      }
    }
  }

  const isDocked = positionMode === 'docked'

  return (
    <aside
      aria-label="ALIAS Companion"
      className={
        isDocked
          ? `relative select-none pointer-events-auto flex items-center justify-center ${className}`
          : `fixed bottom-7 right-7 z-40 select-none pointer-events-auto ${className}`
      }
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <AnimatePresence mode="wait">
        {isMinimized ? (
          /* Minimized Compact Orb */
          <motion.button
            key="minimized-orb"
            initial={{ scale: 0.6, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.6, opacity: 0 }}
            whileHover={{ scale: 1.12 }}
            whileTap={{ scale: 0.94 }}
            onClick={() => setIsMinimized(false)}
            className="group relative flex items-center justify-center w-12 h-12 rounded-full bg-black/40 backdrop-blur-md border border-lime-400/30 shadow-[0_0_18px_rgba(132,204,22,0.35)] cursor-pointer"
            title="Restore ALIAS Companion"
          >
            {/* Ambient Pulse Glow */}
            <div className="absolute inset-0 rounded-full bg-lime-500/20 blur-md animate-pulse" />

            {/* Micro Avatar Icon */}
            <div className="relative z-10 w-9 h-9 flex items-center justify-center" style={getAvatarGlowStyle()}>
              <Avatar
                definition={definition || defaultAlienDef}
                animation={activeAnim}
                size={34}
              />
            </div>

            {/* Live Indicator Dot */}
            <span className={`absolute top-0.5 right-0.5 w-2.5 h-2.5 rounded-full ring-2 ring-black ${
              isListening ? 'bg-cyan-400 animate-ping' :
              activeAnim === 'thinking' ? 'bg-amber-400 animate-pulse' :
              activeAnim === 'working' ? 'bg-indigo-400 animate-pulse' :
              'bg-lime-400'
            }`} />
          </motion.button>
        ) : (
          /* Character Companion Stage */
          <div className="relative flex flex-col items-center">
            
            {/* Dynamic Thought / Speech Bubble */}
            <AnimatePresence>
              {showSpeechBubble && !bubbleDismissed && displayBubbleText && (
                <motion.div
                  key="thought-bubble"
                  initial={{ opacity: 0, y: 8, scale: 0.92 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 6, scale: 0.92 }}
                  transition={{ type: 'spring', stiffness: 400, damping: 28 }}
                  className={`absolute bottom-full mb-2 z-30 flex flex-col items-end pointer-events-auto ${
                    isDocked ? 'right-0' : 'right-0'
                  }`}
                  style={{ minWidth: '180px', maxWidth: '300px' }}
                >
                  {/* Main Cloud Bubble Container */}
                  <div className="relative w-max max-w-[280px] sm:max-w-[310px] px-3.5 py-2.5 bg-white text-gray-900 rounded-[20px] shadow-[0_10px_32px_rgba(0,0,0,0.25)] border border-gray-100/90">
                    <p className="text-[12.5px] font-normal leading-relaxed text-gray-800 break-words">
                      {displayBubbleText}
                    </p>

                    {/* Small dismiss button on hover */}
                    {isHovered && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setBubbleDismissed(true)
                        }}
                        className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-gray-200 hover:bg-gray-300 text-gray-600 flex items-center justify-center text-[10px] shadow-sm transition-colors cursor-pointer"
                        title="Dismiss bubble"
                      >
                        <X size={10} />
                      </button>
                    )}
                  </div>

                  {/* Cascading Circular Thought Dots (Connecting directly down to the character's antenna) */}
                  <div className="flex flex-col items-center mr-6 -mt-0.5 space-y-1">
                    <motion.div
                      animate={{ scale: [1, 1.08, 1] }}
                      transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut' }}
                      className="w-3 h-3 rounded-full bg-white shadow-[0_3px_10px_rgba(0,0,0,0.12)] border border-gray-100/60"
                    />
                    <motion.div
                      animate={{ scale: [1, 1.12, 1] }}
                      transition={{ duration: 2.8, repeat: Infinity, ease: 'easeInOut', delay: 0.2 }}
                      className="w-1.5 h-1.5 rounded-full bg-white shadow-[0_2px_6px_rgba(0,0,0,0.1)] border border-gray-100/60"
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Character Graphic Container */}
            <motion.div
              variants={floatingVariants}
              animate="float"
              className="relative flex flex-col items-center justify-center"
            >
              {/* Interactive Avatar Graphic */}
              <div
                onClick={handlePoke}
                className="relative cursor-pointer group flex items-center justify-center transition-transform active:scale-95 shrink-0"
                title={`Click to interact with ${definition?.name || 'ALIAS'}!`}
                style={getAvatarGlowStyle()}
              >
                <Avatar
                  definition={definition || defaultAlienDef}
                  animation={customAnimation ? customAnimation : (expression ? undefined : activeAnim)}
                  expression={customAnimation ? undefined : (expression || undefined)}
                  size={size}
                />
              </div>

              {/* Quick Floating Micro Actions on Hover */}
              <AnimatePresence>
                {isHovered && (
                  <motion.div
                    initial={{ opacity: 0, y: 4, scale: 0.9 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 4, scale: 0.9 }}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/75 dark:bg-[#1a1a1a]/90 backdrop-blur-md border border-white/15 shadow-xl text-white text-xs z-40 ${
                      isDocked
                        ? 'absolute top-full mt-1.5 left-1/2 -translate-x-1/2 whitespace-nowrap'
                        : 'mt-2'
                    }`}
                  >
                    {onToggleVoice && (
                      <button
                        onClick={onToggleVoice}
                        className={`p-1.5 rounded-full transition-colors cursor-pointer ${
                          isListening
                            ? 'bg-red-500 text-white animate-pulse'
                            : 'hover:bg-white/20 text-gray-200 hover:text-white'
                        }`}
                        title={isListening ? 'Listening active (click to toggle)' : 'Voice Input'}
                      >
                        <Mic size={12} />
                      </button>
                    )}

                    {onStopTTS && (
                      <button
                        onClick={onStopTTS}
                        className="p-1.5 rounded-full hover:bg-red-500/30 text-gray-200 hover:text-red-300 transition-colors cursor-pointer"
                        title="Stop Voice Speech"
                      >
                        <VolumeX size={12} />
                      </button>
                    )}

                    <button
                      onClick={handlePoke}
                      className="p-1.5 rounded-full hover:bg-lime-500/30 text-lime-400 transition-colors cursor-pointer"
                      title="Cheer ALIAS up"
                    >
                      <Sparkles size={12} />
                    </button>

                    <button
                      onClick={() => setIsMinimized(true)}
                      className="p-1.5 rounded-full hover:bg-white/20 text-gray-300 hover:text-white transition-colors cursor-pointer"
                      title="Minimize Companion"
                    >
                      <ChevronDown size={12} />
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </aside>
  )
}
