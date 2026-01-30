import { X, Save, Mic, Monitor } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'

export default function SettingsModal({ isOpen, onClose, theme, setTheme, voice, setVoice }) {
    if (!isOpen) return null

    const [activeTab, setActiveTab] = useState('general')

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ duration: 0.2 }}
                        className="bg-white dark:bg-[#171717] border border-gray-200 dark:border-white/10 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl"
                    >

                        {/* Header */}
                        <div className="p-6 border-b border-gray-200 dark:border-white/5 flex justify-between items-center">
                            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Settings</h2>
                            <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-full transition-colors text-gray-500 dark:text-white/50 hover:text-gray-900 dark:hover:text-white">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="flex h-[450px]">
                            {/* Sidebar */}
                            <div className="w-1/3 border-r border-gray-200 dark:border-white/5 p-3 space-y-1 bg-gray-50 dark:bg-[#171717]">
                                <button
                                    onClick={() => setActiveTab('general')}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'general' ? 'bg-gray-200 dark:bg-[#2f2f2f] text-gray-900 dark:text-white' : 'text-gray-500 dark:text-white/50 hover:bg-gray-100 dark:hover:bg-[#2f2f2f]/50 hover:text-gray-900 dark:hover:text-white'}`}
                                >
                                    <Monitor className="w-4 h-4" />
                                    <span className="text-sm font-medium">General</span>
                                </button>
                                <button
                                    onClick={() => setActiveTab('voice')}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'voice' ? 'bg-gray-200 dark:bg-[#2f2f2f] text-gray-900 dark:text-white' : 'text-gray-500 dark:text-white/50 hover:bg-gray-100 dark:hover:bg-[#2f2f2f]/50 hover:text-gray-900 dark:hover:text-white'}`}
                                >
                                    <Mic className="w-4 h-4" />
                                    <span className="text-sm font-medium">Voice</span>
                                </button>
                            </div>

                            {/* Content */}
                            <div className="flex-1 p-6 overflow-y-auto bg-white dark:bg-[#212121]">
                                {activeTab === 'general' && (
                                    <div className="space-y-6">
                                        <div className="space-y-3">
                                            <label className="text-sm font-medium text-gray-700 dark:text-white/70">Theme</label>
                                            <div className="grid grid-cols-3 gap-3">
                                                <button
                                                    onClick={() => setTheme('dark')}
                                                    className={`p-3 rounded-lg border text-sm font-medium transition-all ${theme === 'dark' ? 'border-gray-900 dark:border-white bg-gray-100 dark:bg-[#2f2f2f] text-gray-900 dark:text-white' : 'border-gray-200 dark:border-white/10 text-gray-500 dark:text-white/50 hover:bg-gray-50 dark:hover:bg-[#2f2f2f]'}`}
                                                >
                                                    Dark
                                                </button>
                                                <button
                                                    onClick={() => setTheme('light')}
                                                    className={`p-3 rounded-lg border text-sm font-medium transition-all ${theme === 'light' ? 'border-gray-900 dark:border-white bg-gray-100 dark:bg-[#2f2f2f] text-gray-900 dark:text-white' : 'border-gray-200 dark:border-white/10 text-gray-500 dark:text-white/50 hover:bg-gray-50 dark:hover:bg-[#2f2f2f]'}`}
                                                >
                                                    Light
                                                </button>
                                                <button
                                                    onClick={() => setTheme('system')}
                                                    className={`p-3 rounded-lg border text-sm font-medium transition-all ${theme === 'system' ? 'border-gray-900 dark:border-white bg-gray-100 dark:bg-[#2f2f2f] text-gray-900 dark:text-white' : 'border-gray-200 dark:border-white/10 text-gray-500 dark:text-white/50 hover:bg-gray-50 dark:hover:bg-[#2f2f2f]'}`}
                                                >
                                                    System
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {activeTab === 'voice' && (
                                    <div className="space-y-6">
                                        <div className="space-y-3">
                                            <label className="text-sm font-medium text-gray-700 dark:text-white/70">Voice Persona</label>
                                            <select
                                                value={voice}
                                                onChange={(e) => setVoice(e.target.value)}
                                                className="w-full bg-gray-50 dark:bg-[#2f2f2f] border border-gray-200 dark:border-white/10 rounded-lg px-4 py-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:border-gray-400 dark:focus:border-white/30"
                                            >
                                                <option value="male">Christopher (Male)</option>
                                                <option value="female">Nova (Female)</option>
                                            </select>
                                            <p className="text-xs text-gray-500 dark:text-white/30">Currently using Edge TTS (Online Neural Voice)</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="p-4 border-t border-gray-200 dark:border-white/5 flex justify-end gap-3 bg-gray-50 dark:bg-[#171717]">
                            <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm font-medium bg-gray-900 dark:bg-white text-white dark:text-black hover:opacity-90 transition-all flex items-center gap-2">
                                <Save className="w-4 h-4" />
                                Done
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    )
}
