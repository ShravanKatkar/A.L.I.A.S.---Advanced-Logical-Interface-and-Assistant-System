import React, { useState } from 'react'
import { X, Play, Sparkles, Sliders, Activity, Info, RefreshCw } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import OneeAvatar from './OneeAvatar'
import avatarDef from '../assets/onee-avatar-definition.json'

export default function AvatarStudioModal({
  isOpen,
  onClose,
  currentAnimation = 'idle',
  onSelectAnimation = null,
  onSelectExpression = null
}) {
  if (!isOpen) return null

  const [activeTab, setActiveTab] = useState('animations') // 'animations' | 'expressions' | 'info'
  const [previewAnimation, setPreviewAnimation] = useState(currentAnimation)
  const [previewExpression, setPreviewExpression] = useState(null)
  const [selectedGroup, setSelectedGroup] = useState('all')

  const groups = ['all', 'Cycle de vie', 'Réactions']

  const handleChooseAnimation = (animKey) => {
    setPreviewExpression(null)
    setPreviewAnimation(animKey)
    if (onSelectAnimation) {
      onSelectAnimation(animKey)
    }
  }

  const handleChooseExpression = (exprKey) => {
    setPreviewExpression(exprKey)
    if (onSelectExpression) {
      onSelectExpression(exprKey)
    }
  }

  const handleResetToAuto = () => {
    setPreviewExpression(null)
    setPreviewAnimation('idle')
    if (onSelectAnimation) {
      onSelectAnimation('idle')
    }
  }

  const filteredAnimations = avatarDef.animationOrder.filter(key => {
    if (selectedGroup === 'all') return true
    const meta = avatarDef.animations[key]?.metadata
    return meta?.group === selectedGroup
  })

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.94 }}
          transition={{ duration: 0.2 }}
          className="bg-white dark:bg-[#181818] border border-gray-200 dark:border-white/10 rounded-3xl w-full max-w-4xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]"
        >
          {/* Header */}
          <div className="p-5 border-b border-gray-200 dark:border-white/5 flex items-center justify-between bg-gray-50/50 dark:bg-white/[0.02]">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center border border-blue-500/20">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <span>Onee Avatar Studio</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 font-semibold border border-blue-500/20 uppercase tracking-wider">
                    v1.0
                  </span>
                </h2>
                <p className="text-xs text-gray-500 dark:text-white/40">
                  Interactive companion expressions, emotion timelines, and animation states
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleResetToAuto}
                className="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-white/10 text-xs font-medium text-gray-600 dark:text-white/70 hover:bg-gray-100 dark:hover:bg-white/10 transition-colors flex items-center gap-1.5"
                title="Reset to automated behavior"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Auto Mode</span>
              </button>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-full transition-colors text-gray-400 hover:text-gray-900 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Main Grid: Left Stage + Right Controls */}
          <div className="flex-1 flex min-h-0 divide-x divide-gray-200 dark:divide-white/5">
            {/* Left: 3D Stage Preview */}
            <div className="w-2/5 p-6 flex flex-col items-center justify-center bg-gradient-to-b from-gray-50 to-white dark:from-[#1b1b1b] dark:to-[#141414] relative">
              <div className="relative">
                <OneeAvatar
                  animation={previewAnimation}
                  expression={previewExpression}
                  size={260}
                  interactive={true}
                  showLabel={true}
                  statusText={previewExpression ? `Expression: ${previewExpression}` : `Animation: ${previewAnimation}`}
                />
              </div>

              <div className="mt-6 text-center max-w-[260px]">
                <div className="text-xs font-medium text-gray-800 dark:text-white/90 capitalize">
                  {previewExpression || previewAnimation}
                </div>
                <p className="text-[11px] text-gray-500 dark:text-white/40 mt-1 leading-relaxed">
                  {previewExpression
                    ? `Head rotation (x:${avatarDef.expressions[previewExpression]?.head?.x.toFixed(1)}, y:${avatarDef.expressions[previewExpression]?.head?.y.toFixed(1)}), Eyes spacing ${avatarDef.expressions[previewExpression]?.eyes?.spacing.toFixed(1)}px`
                    : avatarDef.animations[previewAnimation]?.metadata?.description || 'Active state'}
                </p>
              </div>
            </div>

            {/* Right: Selectors & Tabs */}
            <div className="flex-1 flex flex-col min-h-0 bg-white dark:bg-[#1a1a1a]">
              {/* Tab Navigation */}
              <div className="flex border-b border-gray-200 dark:border-white/5 p-2 gap-1 bg-gray-50/50 dark:bg-white/[0.01]">
                <button
                  onClick={() => setActiveTab('animations')}
                  className={`flex-1 py-2 px-3 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-2 ${
                    activeTab === 'animations'
                      ? 'bg-white dark:bg-[#282828] text-gray-900 dark:text-white shadow-sm border border-gray-200 dark:border-white/10'
                      : 'text-gray-500 dark:text-white/50 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <Activity className="w-3.5 h-3.5" />
                  <span>Animations ({avatarDef.animationOrder.length})</span>
                </button>
                <button
                  onClick={() => setActiveTab('expressions')}
                  className={`flex-1 py-2 px-3 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-2 ${
                    activeTab === 'expressions'
                      ? 'bg-white dark:bg-[#282828] text-gray-900 dark:text-white shadow-sm border border-gray-200 dark:border-white/10'
                      : 'text-gray-500 dark:text-white/50 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <Sliders className="w-3.5 h-3.5" />
                  <span>Expressions ({avatarDef.expressionOrder.length})</span>
                </button>
                <button
                  onClick={() => setActiveTab('info')}
                  className={`py-2 px-3 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-2 ${
                    activeTab === 'info'
                      ? 'bg-white dark:bg-[#282828] text-gray-900 dark:text-white shadow-sm border border-gray-200 dark:border-white/10'
                      : 'text-gray-500 dark:text-white/50 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <Info className="w-3.5 h-3.5" />
                  <span>Schema</span>
                </button>
              </div>

              {/* Tab Content */}
              <div className="flex-1 p-5 overflow-y-auto">
                {activeTab === 'animations' && (
                  <div className="space-y-4">
                    {/* Filter Pills */}
                    <div className="flex gap-1.5 pb-1">
                      {groups.map(grp => (
                        <button
                          key={grp}
                          onClick={() => setSelectedGroup(grp)}
                          className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all capitalize ${
                            selectedGroup === grp
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-white/50 hover:bg-gray-200 dark:hover:bg-white/10'
                          }`}
                        >
                          {grp === 'all' ? 'All Animations' : grp}
                        </button>
                      ))}
                    </div>

                    {/* Animation Cards Grid */}
                    <div className="grid grid-cols-2 gap-2.5">
                      {filteredAnimations.map(key => {
                        const anim = avatarDef.animations[key]
                        const isSelected = previewAnimation === key && !previewExpression
                        return (
                          <button
                            key={key}
                            onClick={() => handleChooseAnimation(key)}
                            className={`p-3 rounded-xl text-left border transition-all flex flex-col justify-between group ${
                              isSelected
                                ? 'bg-blue-50 dark:bg-blue-950/30 border-blue-500/50 dark:border-blue-500/50 shadow-sm'
                                : 'bg-gray-50 dark:bg-[#222222] border-gray-100 dark:border-white/5 hover:border-gray-300 dark:hover:border-white/15'
                            }`}
                          >
                            <div className="flex items-center justify-between w-full">
                              <span className={`text-xs font-semibold capitalize ${isSelected ? 'text-blue-600 dark:text-blue-400' : 'text-gray-900 dark:text-white'}`}>
                                {key}
                              </span>
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-200/60 dark:bg-white/10 text-gray-500 dark:text-white/40">
                                {anim.steps?.length} steps
                              </span>
                            </div>
                            <p className="text-[11px] text-gray-500 dark:text-white/40 mt-1 line-clamp-2">
                              {anim.metadata?.description || 'Animation sequence'}
                            </p>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                {activeTab === 'expressions' && (
                  <div className="space-y-3">
                    <p className="text-xs text-gray-500 dark:text-white/40 mb-3">
                      Select any discrete expression to test head orientation, eye apertures, and angles:
                    </p>
                    <div className="grid grid-cols-3 gap-2">
                      {avatarDef.expressionOrder.map(key => {
                        const expr = avatarDef.expressions[key]
                        const isSelected = previewExpression === key
                        return (
                          <button
                            key={key}
                            onClick={() => handleChooseExpression(key)}
                            className={`p-2.5 rounded-xl text-left border transition-all ${
                              isSelected
                                ? 'bg-purple-50 dark:bg-purple-950/30 border-purple-500/50 dark:border-purple-500/50 text-purple-700 dark:text-purple-300 font-medium'
                                : 'bg-gray-50 dark:bg-[#222222] border-gray-100 dark:border-white/5 hover:border-gray-300 dark:hover:border-white/15 text-gray-800 dark:text-white/80 text-xs'
                            }`}
                          >
                            <div className="truncate capitalize text-xs">{key.replace(/-/g, ' ')}</div>
                            <div className="text-[9px] text-gray-400 dark:text-white/30 mt-0.5">
                              yaw: {expr.head.y.toFixed(0)}° / pitch: {expr.head.x.toFixed(0)}°
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                {activeTab === 'info' && (
                  <div className="space-y-4 text-xs text-gray-700 dark:text-white/80">
                    <div className="p-4 bg-gray-50 dark:bg-[#222222] rounded-xl border border-gray-100 dark:border-white/5 space-y-2">
                      <div className="font-semibold text-gray-900 dark:text-white">Avatar Specification</div>
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div><span className="text-gray-400">Name:</span> {avatarDef.name}</div>
                        <div><span className="text-gray-400">Schema:</span> {avatarDef.schema}</div>
                        <div><span className="text-gray-400">Body Type:</span> {avatarDef.body.primary.type}</div>
                        <div><span className="text-gray-400">Body Color:</span> {avatarDef.colors.body}</div>
                        <div><span className="text-gray-400">Expressions:</span> {avatarDef.expressionOrder.length} defined</div>
                        <div><span className="text-gray-400">Animations:</span> {avatarDef.animationOrder.length} defined</div>
                      </div>
                    </div>

                    <div className="p-4 bg-blue-50/50 dark:bg-blue-950/20 rounded-xl border border-blue-200 dark:border-blue-500/20 text-[11px] leading-relaxed text-blue-800 dark:text-blue-300">
                      <strong>Dynamic Mood Integration:</strong> Onee automatically transitions between animations based on your workflow:
                      <ul className="list-disc pl-4 mt-1.5 space-y-1">
                        <li><strong>Listening:</strong> Active when speaking or using voice dictation</li>
                        <li><strong>Thinking:</strong> Active during model inference and tool evaluation</li>
                        <li><strong>Working:</strong> Active while streaming code blocks, generating PDFs/Word docs, or rendering images</li>
                        <li><strong>Celebrate/Happy:</strong> Triggered upon successful completion</li>
                        <li><strong>Sleeping/Drowsy:</strong> Triggered during extended periods of user inactivity</li>
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
