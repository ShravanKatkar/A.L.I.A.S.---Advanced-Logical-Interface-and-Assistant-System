import { X, Save, Mic, Monitor, Brain, Trash2, Key, CheckCircle, AlertCircle, Eye, EyeOff, Loader2, Bot, Sparkles, Sliders, Smile } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect } from 'react'
import { Avatar } from '@bible-strong/avatar-react'

const AVATAR_EXPRESSIONS = [
    { key: null, name: 'Auto (Dynamic)', desc: 'Intelligently shifts mood based on conversation context' },
    { key: 'neutral', name: 'Neutral', desc: 'Calm & balanced during normal chat' },
    { key: 'joyful-wide', name: 'Joyful', desc: 'Cheerful & smiling on celebrations' },
    { key: 'playful-right', name: 'Playful', desc: 'Sideways glance on hi/hey & output ready' },
    { key: 'curious-left', name: 'Curious', desc: 'Head tilt while processing question' },
    { key: 'attentive-left', name: 'Focused', desc: 'Concentration while generating images' },
    { key: 'surprised-left', name: 'Surprised', desc: 'Wide alert eyes when error occurs' },
    { key: 'sleepy-squint', name: 'Sleepy', desc: 'Chill resting eyes when there is no work' },
    { key: 'skeptical-left', name: 'Skeptical', desc: 'Analytical raised-eye on doubts & warnings' },
    { key: 'shy-downward', name: 'Gentle / Shy', desc: 'Soft downward gaze on bye & compliments' },
]

export default function SettingsModal({
    isOpen,
    onClose,
    theme,
    setTheme,
    voice,
    setVoice,
    memories = [],
    onDeleteMemory,
    avatarPreset = 'alien',
    onSelectAvatarPreset = () => {},
    avatarPresets = {},
    companionSettings = {},
    onUpdateCompanionSettings = () => {},
    initialTab = 'general'
}) {
    if (!isOpen) return null

    const [activeTab, setActiveTab] = useState(initialTab || 'general')

    useEffect(() => {
        if (isOpen && initialTab) {
            setActiveTab(initialTab)
        }
    }, [isOpen, initialTab])
    
    // API Keys state
    const [keyStatus, setKeyStatus] = useState(null)
    const [loadingKeys, setLoadingKeys] = useState(false)
    const [savingKeys, setSavingKeys] = useState(false)
    const [saveMessage, setSaveMessage] = useState(null)
    
    const [keysInput, setKeysInput] = useState({
        gemini_key: '',
        groq_key: '',
        deepseek_key: '',
        openai_key: ''
    })

    const [visibleKeys, setVisibleKeys] = useState({
        gemini: false,
        groq: false,
        deepseek: false,
        openai: false
    })

    const [testResults, setTestResults] = useState({})
    const [testingProvider, setTestingProvider] = useState(null)

    // Fetch API keys status when modal opens or keys tab is clicked
    useEffect(() => {
        if (isOpen) {
            fetchKeyStatus()
        }
    }, [isOpen, activeTab])

    const fetchKeyStatus = async () => {
        try {
            setLoadingKeys(true)
            const res = await fetch('http://localhost:8000/api/settings/keys')
            if (res.ok) {
                const data = await res.json()
                setKeyStatus(data)
            }
        } catch (e) {
            console.error('Error fetching API key status:', e)
        } finally {
            setLoadingKeys(false)
        }
    }

    const handleTestKey = async (provider) => {
        const key = keysInput[`${provider}_key`] || ''
        if (!key) {
            setTestResults(prev => ({
                ...prev,
                [provider]: { success: false, message: 'Please enter a key to test.' }
            }))
            return
        }

        try {
            setTestingProvider(provider)
            const res = await fetch('http://localhost:8000/api/settings/keys/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider, key })
            })
            const data = await res.json()
            setTestResults(prev => ({ ...prev, [provider]: data }))
        } catch (e) {
            setTestResults(prev => ({
                ...prev,
                [provider]: { success: false, message: 'Could not contact server to test key.' }
            }))
        } finally {
            setTestingProvider(null)
        }
    }

    const handleSaveKeys = async () => {
        try {
            setSavingKeys(true)
            setSaveMessage(null)

            const payload = {}
            if (keysInput.gemini_key.trim()) payload.gemini_key = keysInput.gemini_key.trim()
            if (keysInput.groq_key.trim()) payload.groq_key = keysInput.groq_key.trim()
            if (keysInput.deepseek_key.trim()) payload.deepseek_key = keysInput.deepseek_key.trim()
            if (keysInput.openai_key.trim()) payload.openai_key = keysInput.openai_key.trim()

            const res = await fetch('http://localhost:8000/api/settings/keys', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })

            const data = await res.json()
            if (res.ok && data.status === 'success') {
                setSaveMessage({ type: 'success', text: 'API keys saved successfully! Available models updated.' })
                if (data.provider_status) {
                    setKeyStatus(data.provider_status)
                }
                // Clear input fields
                setKeysInput({ gemini_key: '', groq_key: '', deepseek_key: '', openai_key: '' })
            } else {
                setSaveMessage({ type: 'error', text: data.message || 'Failed to save keys.' })
            }
        } catch (e) {
            setSaveMessage({ type: 'error', text: 'Connection failed while saving keys.' })
        } finally {
            setSavingKeys(false)
        }
    }

    const toggleVisibility = (prov) => {
        setVisibleKeys(prev => ({ ...prev, [prov]: !prev[prov] }))
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
                        className="bg-white dark:bg-[#171717] border border-gray-200 dark:border-white/10 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl"
                    >

                        {/* Header */}
                        <div className="p-6 border-b border-gray-200 dark:border-white/5 flex justify-between items-center">
                            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Settings</h2>
                            <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-full transition-colors text-gray-500 dark:text-white/50 hover:text-gray-900 dark:hover:text-white">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="flex h-[470px]">
                            {/* Sidebar */}
                            <div className="w-1/3 border-r border-gray-200 dark:border-white/5 p-3 space-y-1 bg-gray-50 dark:bg-[#171717]">
                                <button
                                    onClick={() => setActiveTab('general')}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'general' ? 'bg-gray-200 dark:bg-[#2f2f2f] text-gray-900 dark:text-white font-medium' : 'text-gray-500 dark:text-white/50 hover:bg-gray-100 dark:hover:bg-[#2f2f2f]/50 hover:text-gray-900 dark:hover:text-white'}`}
                                >
                                    <Monitor className="w-4 h-4" />
                                    <span className="text-sm">General</span>
                                </button>
                                <button
                                    onClick={() => setActiveTab('avatar')}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'avatar' ? 'bg-gray-200 dark:bg-[#2f2f2f] text-gray-900 dark:text-white font-medium' : 'text-gray-500 dark:text-white/50 hover:bg-gray-100 dark:hover:bg-[#2f2f2f]/50 hover:text-gray-900 dark:hover:text-white'}`}
                                >
                                    <Bot className="w-4 h-4" />
                                    <span className="text-sm">Avatar</span>
                                </button>
                                <button
                                    onClick={() => setActiveTab('keys')}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'keys' ? 'bg-gray-200 dark:bg-[#2f2f2f] text-gray-900 dark:text-white font-medium' : 'text-gray-500 dark:text-white/50 hover:bg-gray-100 dark:hover:bg-[#2f2f2f]/50 hover:text-gray-900 dark:hover:text-white'}`}
                                >
                                    <Key className="w-4 h-4" />
                                    <span className="text-sm">API Keys</span>
                                </button>
                                <button
                                    onClick={() => setActiveTab('voice')}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'voice' ? 'bg-gray-200 dark:bg-[#2f2f2f] text-gray-900 dark:text-white font-medium' : 'text-gray-500 dark:text-white/50 hover:bg-gray-100 dark:hover:bg-[#2f2f2f]/50 hover:text-gray-900 dark:hover:text-white'}`}
                                >
                                    <Mic className="w-4 h-4" />
                                    <span className="text-sm">Voice</span>
                                </button>
                                <button
                                    onClick={() => setActiveTab('memory')}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'memory' ? 'bg-gray-200 dark:bg-[#2f2f2f] text-gray-900 dark:text-white font-medium' : 'text-gray-500 dark:text-white/50 hover:bg-gray-100 dark:hover:bg-[#2f2f2f]/50 hover:text-gray-900 dark:hover:text-white'}`}
                                >
                                    <Brain className="w-4 h-4" />
                                    <span className="text-sm">Memory</span>
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

                                {activeTab === 'avatar' && (
                                    <div className="space-y-6">
                                        <div>
                                            <h3 className="text-sm font-medium text-gray-800 dark:text-white/80">Avatar & Companion</h3>
                                            <p className="text-xs text-gray-500 dark:text-white/40 mt-0.5">
                                                Choose your companion character, adjust size to align perfectly with the chat box, and customize visuals.
                                            </p>
                                        </div>

                                        {/* Avatar Character Preset Grid */}
                                        <div className="space-y-2.5">
                                            <label className="text-xs font-semibold text-gray-700 dark:text-white/70">
                                                Character Model
                                            </label>
                                            <div className="grid grid-cols-2 gap-3">
                                                {Object.entries(avatarPresets).map(([key, item]) => {
                                                    const isSelected = avatarPreset === key
                                                    return (
                                                        <button
                                                            key={key}
                                                            type="button"
                                                            onClick={() => onSelectAvatarPreset(key)}
                                                            className={`p-3 rounded-xl border text-left transition-all flex items-center gap-3 relative cursor-pointer ${
                                                                isSelected
                                                                    ? 'border-gray-900 dark:border-white bg-gray-100 dark:bg-[#2f2f2f] ring-1 ring-black/10 dark:ring-white/20 shadow-sm'
                                                                    : 'border-gray-200 dark:border-white/10 hover:border-gray-300 dark:hover:border-white/20 bg-gray-50/50 dark:bg-[#1a1a1a]'
                                                            }`}
                                                        >
                                                            <div className="w-11 h-11 rounded-full bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 flex items-center justify-center shrink-0">
                                                                <Avatar
                                                                    definition={item.def}
                                                                    animation={isSelected ? "happy" : "idle"}
                                                                    size={36}
                                                                />
                                                            </div>
                                                            <div className="min-w-0 flex-1">
                                                                <div className="flex items-center justify-between">
                                                                    <span className="text-xs font-semibold text-gray-900 dark:text-white truncate">
                                                                        {item.name}
                                                                    </span>
                                                                    {isSelected && (
                                                                        <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0 ml-1" />
                                                                    )}
                                                                </div>
                                                                <p className="text-[11px] text-gray-500 dark:text-white/40 truncate mt-0.5">
                                                                    {item.desc || 'AI Companion'}
                                                                </p>
                                                            </div>
                                                        </button>
                                                    )
                                                })}
                                            </div>
                                        </div>

                                        {/* Avatar Expression & Mood Customization */}
                                        <div className="space-y-2.5">
                                            <div className="flex items-center justify-between">
                                                <label className="text-xs font-semibold text-gray-700 dark:text-white/70 flex items-center gap-1.5">
                                                    <Smile className="w-3.5 h-3.5" />
                                                    Expression & Mood
                                                </label>
                                                <span className="text-[11px] font-medium text-gray-500 dark:text-white/50 bg-gray-100 dark:bg-white/10 px-2 py-0.5 rounded">
                                                    {companionSettings.customExpression
                                                        ? AVATAR_EXPRESSIONS.find(e => e.key === companionSettings.customExpression)?.name || 'Custom'
                                                        : 'Auto (Dynamic)'}
                                                </span>
                                            </div>
                                            <p className="text-[11px] text-gray-500 dark:text-white/40 -mt-0.5">
                                                Select a fixed emotion or let the avatar adapt dynamically to the conversation.
                                            </p>

                                            {/* Auto Dynamic Mode Button */}
                                            <button
                                                type="button"
                                                onClick={() => onUpdateCompanionSettings({ customExpression: null })}
                                                className={`w-full p-2.5 rounded-xl border text-left transition-all flex items-center justify-between cursor-pointer ${
                                                    !companionSettings.customExpression
                                                        ? 'border-gray-900 dark:border-white bg-gray-100 dark:bg-[#2f2f2f] ring-1 ring-black/10 dark:ring-white/20 shadow-sm'
                                                        : 'border-gray-200 dark:border-white/10 hover:border-gray-300 dark:hover:border-white/20 bg-gray-50/50 dark:bg-[#1a1a1a]'
                                                }`}
                                            >
                                                <div className="flex items-center gap-2.5 min-w-0">
                                                    <div className="w-8 h-8 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
                                                        <Sparkles className="w-4 h-4" />
                                                    </div>
                                                    <div className="min-w-0">
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-xs font-semibold text-gray-900 dark:text-white">Auto (Dynamic)</span>
                                                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-medium">
                                                                Default
                                                            </span>
                                                        </div>
                                                        <p className="text-[11px] text-gray-500 dark:text-white/40 truncate">
                                                            Reacts in real-time when listening, thinking, speaking, or idle.
                                                        </p>
                                                    </div>
                                                </div>
                                                {!companionSettings.customExpression && (
                                                    <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0 ml-2" />
                                                )}
                                            </button>

                                            {/* Curated Fixed Expressions Grid */}
                                            <div className="grid grid-cols-3 gap-2 pt-1">
                                                {AVATAR_EXPRESSIONS.filter(e => e.key !== null).map((item) => {
                                                    const isSelected = companionSettings.customExpression === item.key
                                                    const activeDef = avatarPresets[avatarPreset]?.def || avatarPresets.alien?.def
                                                    return (
                                                        <button
                                                            key={item.key}
                                                            type="button"
                                                            onClick={() => onUpdateCompanionSettings({ customExpression: item.key })}
                                                            className={`p-2.5 rounded-xl border text-left transition-all flex flex-col items-center text-center cursor-pointer relative group ${
                                                                isSelected
                                                                    ? 'border-gray-900 dark:border-white bg-gray-100 dark:bg-[#2f2f2f] ring-1 ring-black/10 dark:ring-white/20 shadow-sm'
                                                                    : 'border-gray-200 dark:border-white/10 hover:border-gray-300 dark:hover:border-white/20 bg-gray-50/50 dark:bg-[#1a1a1a]'
                                                            }`}
                                                        >
                                                            <div className="w-9 h-9 rounded-full bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 flex items-center justify-center mb-1.5 overflow-hidden shrink-0">
                                                                <Avatar
                                                                    definition={activeDef}
                                                                    expression={item.key}
                                                                    size={30}
                                                                />
                                                            </div>
                                                            <div className="w-full">
                                                                <div className="flex items-center justify-center gap-1">
                                                                    <span className="text-[11px] font-semibold text-gray-900 dark:text-white truncate">
                                                                        {item.name}
                                                                    </span>
                                                                    {isSelected && (
                                                                        <CheckCircle className="w-3 h-3 text-emerald-500 shrink-0" />
                                                                    )}
                                                                </div>
                                                                <p className="text-[10px] text-gray-500 dark:text-white/40 truncate leading-tight mt-0.5">
                                                                    {item.desc}
                                                                </p>
                                                            </div>
                                                        </button>
                                                    )
                                                })}
                                            </div>
                                        </div>

                                        {/* Alignment & Placement */}
                                        <div className="space-y-2.5">
                                            <label className="text-xs font-semibold text-gray-700 dark:text-white/70">
                                                Alignment & Placement
                                            </label>
                                            <div className="grid grid-cols-2 gap-3">
                                                <button
                                                    type="button"
                                                    onClick={() => onUpdateCompanionSettings({ positionMode: 'docked' })}
                                                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                                                        companionSettings.positionMode === 'docked' || !companionSettings.positionMode
                                                            ? 'border-gray-900 dark:border-white bg-gray-100 dark:bg-[#2f2f2f] ring-1 ring-black/10 dark:ring-white/20 shadow-sm'
                                                            : 'border-gray-200 dark:border-white/10 bg-gray-50/50 dark:bg-[#1a1a1a] hover:border-gray-300'
                                                    }`}
                                                >
                                                    <div className="flex items-center justify-between mb-1">
                                                        <span className="text-xs font-semibold text-gray-900 dark:text-white">
                                                            Beside Text Box
                                                        </span>
                                                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-medium">
                                                            Recommended
                                                        </span>
                                                    </div>
                                                    <p className="text-[11px] text-gray-500 dark:text-white/40 leading-snug">
                                                        Neatly aligned alongside the message input box.
                                                    </p>
                                                </button>

                                                <button
                                                    type="button"
                                                    onClick={() => onUpdateCompanionSettings({ positionMode: 'floating' })}
                                                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${
                                                        companionSettings.positionMode === 'floating'
                                                            ? 'border-gray-900 dark:border-white bg-gray-100 dark:bg-[#2f2f2f] ring-1 ring-black/10 dark:ring-white/20 shadow-sm'
                                                            : 'border-gray-200 dark:border-white/10 bg-gray-50/50 dark:bg-[#1a1a1a] hover:border-gray-300'
                                                    }`}
                                                >
                                                    <div className="flex items-center justify-between mb-1">
                                                        <span className="text-xs font-semibold text-gray-900 dark:text-white">
                                                            Floating Corner
                                                        </span>
                                                    </div>
                                                    <p className="text-[11px] text-gray-500 dark:text-white/40 leading-snug">
                                                        Floats in the bottom-right corner of the window.
                                                    </p>
                                                </button>
                                            </div>
                                        </div>

                                        {/* Avatar Size Adjustment */}
                                        <div className="space-y-2.5">
                                            <div className="flex items-center justify-between">
                                                <label className="text-xs font-semibold text-gray-700 dark:text-white/70">
                                                    Avatar Size
                                                </label>
                                                <span className="text-xs font-mono font-medium text-gray-900 dark:text-white bg-gray-100 dark:bg-white/10 px-2 py-0.5 rounded">
                                                    {companionSettings.size || 78}px
                                                </span>
                                            </div>
                                            <input
                                                type="range"
                                                min={54}
                                                max={120}
                                                step={2}
                                                value={companionSettings.size || 78}
                                                onChange={(e) => onUpdateCompanionSettings({ size: Number(e.target.value) })}
                                                className="w-full accent-black dark:accent-white cursor-pointer h-1.5 bg-gray-200 dark:bg-white/20 rounded-lg appearance-none"
                                            />
                                            <div className="flex items-center gap-2 pt-1">
                                                {[
                                                    { label: 'Compact', size: 64 },
                                                    { label: 'Matched (78px)', size: 78 },
                                                    { label: 'Medium', size: 92 },
                                                    { label: 'Large', size: 110 }
                                                ].map(preset => (
                                                    <button
                                                        key={preset.label}
                                                        type="button"
                                                        onClick={() => onUpdateCompanionSettings({ size: preset.size })}
                                                        className={`px-2.5 py-1 text-[11px] rounded-lg border transition-all cursor-pointer ${
                                                            (companionSettings.size || 78) === preset.size
                                                                ? 'bg-black dark:bg-white text-white dark:text-black border-transparent font-medium shadow-sm'
                                                                : 'border-gray-200 dark:border-white/10 text-gray-600 dark:text-white/60 hover:bg-gray-100 dark:hover:bg-white/5'
                                                        }`}
                                                    >
                                                        {preset.label}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Visual and Behavioral Toggles */}
                                        <div className="space-y-3 pt-2 border-t border-gray-200 dark:border-white/5">
                                            {/* Enable Animated Companion */}
                                            <div className="flex items-center justify-between py-1">
                                                <div>
                                                    <div className="text-xs font-semibold text-gray-900 dark:text-white">Enable Animated Companion</div>
                                                    <p className="text-[11px] text-gray-500 dark:text-white/40">Show the interactive avatar on your desktop chat.</p>
                                                </div>
                                                <input
                                                    type="checkbox"
                                                    checked={companionSettings.enabled !== false}
                                                    onChange={(e) => onUpdateCompanionSettings({ enabled: e.target.checked })}
                                                    className="w-4 h-4 accent-black dark:accent-white rounded cursor-pointer"
                                                />
                                            </div>

                                            {/* Show Thought & Speech Bubbles */}
                                            <div className="flex items-center justify-between py-1">
                                                <div>
                                                    <div className="text-xs font-semibold text-gray-900 dark:text-white">Thought & Speech Bubbles</div>
                                                    <p className="text-[11px] text-gray-500 dark:text-white/40">Display speech bubble with assistant thoughts above the avatar.</p>
                                                </div>
                                                <input
                                                    type="checkbox"
                                                    checked={companionSettings.showSpeechBubble !== false}
                                                    onChange={(e) => onUpdateCompanionSettings({ showSpeechBubble: e.target.checked })}
                                                    className="w-4 h-4 accent-black dark:accent-white rounded cursor-pointer"
                                                />
                                            </div>

                                            {/* Neon Glow Bloom */}
                                            <div className="flex items-center justify-between py-1">
                                                <div>
                                                    <div className="text-xs font-semibold text-gray-900 dark:text-white">Atmospheric Glow Bloom</div>
                                                    <p className="text-[11px] text-gray-500 dark:text-white/40">Soft ambient glow surrounding the character.</p>
                                                </div>
                                                <input
                                                    type="checkbox"
                                                    checked={companionSettings.enableGlow !== false}
                                                    onChange={(e) => onUpdateCompanionSettings({ enableGlow: e.target.checked })}
                                                    className="w-4 h-4 accent-black dark:accent-white rounded cursor-pointer"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                )}

                                {activeTab === 'keys' && (
                                    <div className="space-y-5">
                                        <div>
                                            <h3 className="text-sm font-medium text-gray-800 dark:text-white/80">AI Provider API Keys</h3>
                                            <p className="text-xs text-gray-500 dark:text-white/40 mt-0.5">
                                                Manage and test API keys for Gemini, Groq, DeepSeek, and OpenAI. Keys are stored locally in your .env file.
                                            </p>
                                        </div>

                                        {saveMessage && (
                                            <div className={`p-3 rounded-lg text-xs flex items-center gap-2 ${saveMessage.type === 'success' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20'}`}>
                                                {saveMessage.type === 'success' ? <CheckCircle className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
                                                <span>{saveMessage.text}</span>
                                            </div>
                                        )}

                                        {/* Gemini */}
                                        <div className="p-3.5 bg-gray-50 dark:bg-[#2a2a2a] rounded-xl border border-gray-100 dark:border-white/5 space-y-2">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-sm font-medium text-gray-900 dark:text-white">Google Gemini</span>
                                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 font-medium">Recommended</span>
                                                </div>
                                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${keyStatus?.gemini?.configured ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' : 'bg-gray-200 dark:bg-white/10 text-gray-500 dark:text-white/40'}`}>
                                                    {keyStatus?.gemini?.configured ? `Active (${keyStatus.gemini.key_masked})` : 'Not Configured'}
                                                </span>
                                            </div>
                                            <div className="flex gap-2">
                                                <div className="relative flex-1">
                                                    <input
                                                        type={visibleKeys.gemini ? "text" : "password"}
                                                        placeholder={keyStatus?.gemini?.configured ? "Enter new key to update..." : "Enter Gemini API key (AIzaSy...)"}
                                                        value={keysInput.gemini_key}
                                                        onChange={(e) => setKeysInput(prev => ({ ...prev, gemini_key: e.target.value }))}
                                                        className="w-full bg-white dark:bg-[#1f1f1f] border border-gray-200 dark:border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-900 dark:text-white pr-8 focus:outline-none focus:border-blue-500"
                                                    />
                                                    <button
                                                        type="button"
                                                        onClick={() => toggleVisibility('gemini')}
                                                        className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-white"
                                                    >
                                                        {visibleKeys.gemini ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                                                    </button>
                                                </div>
                                                <button
                                                    onClick={() => handleTestKey('gemini')}
                                                    disabled={testingProvider === 'gemini'}
                                                    className="px-3 py-1.5 bg-gray-200 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/15 rounded-lg text-xs font-medium text-gray-800 dark:text-white transition-all disabled:opacity-50"
                                                >
                                                    {testingProvider === 'gemini' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Test"}
                                                </button>
                                            </div>
                                            {testResults.gemini && (
                                                <p className={`text-[11px] ${testResults.gemini.success ? 'text-emerald-500' : 'text-red-400'}`}>
                                                    {testResults.gemini.message}
                                                </p>
                                            )}
                                        </div>

                                        {/* Groq */}
                                        <div className="p-3.5 bg-gray-50 dark:bg-[#2a2a2a] rounded-xl border border-gray-100 dark:border-white/5 space-y-2">
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-sm font-medium text-gray-900 dark:text-white">Groq Cloud</span>
                                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 font-medium">Ultra Fast</span>
                                                </div>
                                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${keyStatus?.groq?.configured ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' : 'bg-gray-200 dark:bg-white/10 text-gray-500 dark:text-white/40'}`}>
                                                    {keyStatus?.groq?.configured ? `Active (${keyStatus.groq.key_masked})` : 'Not Configured'}
                                                </span>
                                            </div>
                                            <div className="flex gap-2">
                                                <div className="relative flex-1">
                                                    <input
                                                        type={visibleKeys.groq ? "text" : "password"}
                                                        placeholder={keyStatus?.groq?.configured ? "Enter new key to update..." : "Enter Groq API key (gsk_...)"}
                                                        value={keysInput.groq_key}
                                                        onChange={(e) => setKeysInput(prev => ({ ...prev, groq_key: e.target.value }))}
                                                        className="w-full bg-white dark:bg-[#1f1f1f] border border-gray-200 dark:border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-900 dark:text-white pr-8 focus:outline-none focus:border-purple-500"
                                                    />
                                                    <button
                                                        type="button"
                                                        onClick={() => toggleVisibility('groq')}
                                                        className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-white"
                                                    >
                                                        {visibleKeys.groq ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                                                    </button>
                                                </div>
                                                <button
                                                    onClick={() => handleTestKey('groq')}
                                                    disabled={testingProvider === 'groq'}
                                                    className="px-3 py-1.5 bg-gray-200 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/15 rounded-lg text-xs font-medium text-gray-800 dark:text-white transition-all disabled:opacity-50"
                                                >
                                                    {testingProvider === 'groq' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Test"}
                                                </button>
                                            </div>
                                            {testResults.groq && (
                                                <p className={`text-[11px] ${testResults.groq.success ? 'text-emerald-500' : 'text-red-400'}`}>
                                                    {testResults.groq.message}
                                                </p>
                                            )}
                                        </div>

                                        {/* DeepSeek */}
                                        <div className="p-3.5 bg-gray-50 dark:bg-[#2a2a2a] rounded-xl border border-gray-100 dark:border-white/5 space-y-2">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm font-medium text-gray-900 dark:text-white">DeepSeek</span>
                                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${keyStatus?.deepseek?.has_balance ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' : (keyStatus?.deepseek?.configured ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400' : 'bg-gray-200 dark:bg-white/10 text-gray-500 dark:text-white/40')}`}>
                                                    {keyStatus?.deepseek?.status || 'Not Configured'}
                                                </span>
                                            </div>
                                            <div className="flex gap-2">
                                                <div className="relative flex-1">
                                                    <input
                                                        type={visibleKeys.deepseek ? "text" : "password"}
                                                        placeholder={keyStatus?.deepseek?.configured ? "Enter new key to update..." : "Enter DeepSeek API key (sk-...)"}
                                                        value={keysInput.deepseek_key}
                                                        onChange={(e) => setKeysInput(prev => ({ ...prev, deepseek_key: e.target.value }))}
                                                        className="w-full bg-white dark:bg-[#1f1f1f] border border-gray-200 dark:border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-900 dark:text-white pr-8 focus:outline-none focus:border-blue-500"
                                                    />
                                                    <button
                                                        type="button"
                                                        onClick={() => toggleVisibility('deepseek')}
                                                        className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-white"
                                                    >
                                                        {visibleKeys.deepseek ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                                                    </button>
                                                </div>
                                                <button
                                                    onClick={() => handleTestKey('deepseek')}
                                                    disabled={testingProvider === 'deepseek'}
                                                    className="px-3 py-1.5 bg-gray-200 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/15 rounded-lg text-xs font-medium text-gray-800 dark:text-white transition-all disabled:opacity-50"
                                                >
                                                    {testingProvider === 'deepseek' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Test"}
                                                </button>
                                            </div>
                                            {testResults.deepseek && (
                                                <p className={`text-[11px] ${testResults.deepseek.success ? 'text-emerald-500' : 'text-red-400'}`}>
                                                    {testResults.deepseek.message}
                                                </p>
                                            )}
                                        </div>

                                        {/* OpenAI */}
                                        <div className="p-3.5 bg-gray-50 dark:bg-[#2a2a2a] rounded-xl border border-gray-100 dark:border-white/5 space-y-2">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm font-medium text-gray-900 dark:text-white">OpenAI</span>
                                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${keyStatus?.openai?.configured ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' : 'bg-gray-200 dark:bg-white/10 text-gray-500 dark:text-white/40'}`}>
                                                    {keyStatus?.openai?.configured ? `Active (${keyStatus.openai.key_masked})` : 'Not Configured'}
                                                </span>
                                            </div>
                                            <div className="flex gap-2">
                                                <div className="relative flex-1">
                                                    <input
                                                        type={visibleKeys.openai ? "text" : "password"}
                                                        placeholder={keyStatus?.openai?.configured ? "Enter new key to update..." : "Enter OpenAI key (sk-... or GitHub token)"}
                                                        value={keysInput.openai_key}
                                                        onChange={(e) => setKeysInput(prev => ({ ...prev, openai_key: e.target.value }))}
                                                        className="w-full bg-white dark:bg-[#1f1f1f] border border-gray-200 dark:border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-900 dark:text-white pr-8 focus:outline-none focus:border-green-500"
                                                    />
                                                    <button
                                                        type="button"
                                                        onClick={() => toggleVisibility('openai')}
                                                        className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-white"
                                                    >
                                                        {visibleKeys.openai ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                                                    </button>
                                                </div>
                                                <button
                                                    onClick={() => handleTestKey('openai')}
                                                    disabled={testingProvider === 'openai'}
                                                    className="px-3 py-1.5 bg-gray-200 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/15 rounded-lg text-xs font-medium text-gray-800 dark:text-white transition-all disabled:opacity-50"
                                                >
                                                    {testingProvider === 'openai' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Test"}
                                                </button>
                                            </div>
                                            {testResults.openai && (
                                                <p className={`text-[11px] ${testResults.openai.success ? 'text-emerald-500' : 'text-red-400'}`}>
                                                    {testResults.openai.message}
                                                </p>
                                            )}
                                        </div>

                                        <div className="pt-2 flex justify-end">
                                            <button
                                                onClick={handleSaveKeys}
                                                disabled={savingKeys}
                                                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg flex items-center gap-2 transition-all shadow-md disabled:opacity-50"
                                            >
                                                {savingKeys ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                                                Save & Apply Keys
                                            </button>
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

                                {activeTab === 'memory' && (
                                    <div className="space-y-4">
                                        <div>
                                            <h3 className="text-sm font-medium text-gray-700 dark:text-white/70 mb-1">Stored Memories</h3>
                                            <p className="text-xs text-gray-500 dark:text-white/40">These are facts ALIAS has learned about you. You can delete facts you want ALIAS to forget.</p>
                                        </div>
                                        {memories.length === 0 ? (
                                            <div className="text-center py-8 text-sm text-gray-400 dark:text-white/30">
                                                No memories stored yet. Converse with ALIAS to share information.
                                            </div>
                                        ) : (
                                            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                                                {memories.map((mem) => (
                                                    <div key={mem.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-[#2f2f2f] border border-gray-100 dark:border-white/5 rounded-xl group hover:border-gray-300 dark:hover:border-white/15 transition-all">
                                                        <span className="text-sm text-gray-800 dark:text-white/90 font-light pr-4">{mem.fact}</span>
                                                        <button
                                                            onClick={() => onDeleteMemory(mem.id)}
                                                            className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-500/10 dark:hover:bg-red-500/20 rounded-lg transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                                                            title="Forget this fact"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
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
