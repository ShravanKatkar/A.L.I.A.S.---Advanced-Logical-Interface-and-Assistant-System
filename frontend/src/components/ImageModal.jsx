import { X, Sparkles, Play } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'

export default function ImageModal({ isOpen, onClose, onGenerate }) {
    const [prompt, setPrompt] = useState('')
    const [model, setModel] = useState('flux')
    const [dimension, setDimension] = useState('1024x1024')

    if (!isOpen) return null

    const handleGenerate = () => {
        if (!prompt.trim()) return
        const [width, height] = dimension.split('x').map(Number)
        onGenerate({ prompt, width, height, model })
        setPrompt('')
        onClose()
    }

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                        className="bg-white dark:bg-[#171717] border border-gray-200 dark:border-white/10 rounded-2xl w-full max-w-xl overflow-hidden shadow-2xl"
                    >
                        {/* Header */}
                        <div className="p-6 border-b border-gray-200 dark:border-white/5 flex justify-between items-center">
                            <div className="flex items-center gap-2">
                                <Sparkles className="w-5 h-5 text-indigo-500 animate-pulse" />
                                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Generate AI Image</h2>
                            </div>
                            <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-full transition-colors text-gray-500 dark:text-white/50 hover:text-gray-900 dark:hover:text-white">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="p-6 space-y-6 bg-white dark:bg-[#212121]">
                            {/* Prompt Input */}
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-[#c9c9c9]">What do you want to create?</label>
                                <textarea
                                    value={prompt}
                                    onChange={(e) => setPrompt(e.target.value)}
                                    placeholder="Describe the image you want to generate in detail (e.g. 'A futuristic city street at night with neon lights...')"
                                    rows={4}
                                    className="w-full bg-gray-50 dark:bg-[#2f2f2f] border border-gray-200 dark:border-white/10 rounded-xl px-4 py-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all resize-none"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                {/* Model Selection */}
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-gray-700 dark:text-[#c9c9c9]">Model</label>
                                    <select
                                        value={model}
                                        onChange={(e) => setModel(e.target.value)}
                                        className="w-full bg-gray-50 dark:bg-[#2f2f2f] border border-gray-200 dark:border-white/10 rounded-xl px-4 py-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all cursor-pointer"
                                    >
                                        <option value="flux">FLUX (High Quality)</option>
                                        <option value="default">Default Model</option>
                                    </select>
                                </div>

                                {/* Dimensions Selection */}
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-gray-700 dark:text-[#c9c9c9]">Dimensions</label>
                                    <select
                                        value={dimension}
                                        onChange={(e) => setDimension(e.target.value)}
                                        className="w-full bg-gray-50 dark:bg-[#2f2f2f] border border-gray-200 dark:border-white/10 rounded-xl px-4 py-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all cursor-pointer"
                                    >
                                        <option value="1024x1024">Square (1024x1024)</option>
                                        <option value="1024x768">Landscape (1024x768)</option>
                                        <option value="768x1024">Portrait (768x1024)</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="p-4 border-t border-gray-200 dark:border-white/5 flex justify-end gap-3 bg-gray-50 dark:bg-[#171717]">
                            <button
                                onClick={onClose}
                                className="px-4 py-2 text-sm font-medium text-gray-500 dark:text-white/70 hover:text-gray-900 dark:hover:text-white transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleGenerate}
                                disabled={!prompt.trim()}
                                className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 shadow-lg ${prompt.trim() ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/10' : 'bg-gray-200 dark:bg-[#2f2f2f] text-gray-400 dark:text-[#424242] cursor-not-allowed shadow-none'}`}
                            >
                                <Play className="w-4 h-4 fill-current" />
                                Generate
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    )
}
