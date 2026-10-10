import { X, Sparkles, Play, ChevronDown, ChevronUp, Zap, Scale, Crown, RefreshCw, Loader2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect } from 'react'

const DEFAULT_CONFIG = {
    models: [
        { id: 'flux', label: 'FLUX (High Quality)', description: 'High-quality image generation', supports_negative_prompt: true, supports_seed: true },
        { id: 'turbo', label: 'Turbo (Fast)', description: 'Faster generation', supports_negative_prompt: true, supports_seed: true },
        { id: 'default', label: 'Default', description: 'Standard model', supports_negative_prompt: false, supports_seed: true },
    ],
    styles: [
        { id: 'none', label: 'None' },
        { id: 'photorealistic', label: 'Photorealistic' },
        { id: 'cinematic', label: 'Cinematic' },
        { id: 'anime', label: 'Anime' },
        { id: 'digital_art', label: 'Digital Art' },
        { id: 'illustration', label: 'Illustration' },
        { id: '3d_render', label: '3D Render' },
        { id: 'oil_painting', label: 'Oil Painting' },
        { id: 'watercolor', label: 'Watercolor' },
    ],
    aspect_ratios: [
        { id: '1:1', label: 'Square', width: 1024, height: 1024 },
        { id: '16:9', label: 'Landscape Wide', width: 1344, height: 768 },
        { id: '9:16', label: 'Portrait Tall', width: 768, height: 1344 },
        { id: '4:3', label: 'Standard', width: 1024, height: 768 },
        { id: '3:2', label: 'Photography', width: 1024, height: 680 },
        { id: '3:4', label: 'Portrait', width: 768, height: 1024 },
    ],
    quality_presets: [
        { id: 'fast', label: 'Fast', description: 'Quick generation' },
        { id: 'balanced', label: 'Balanced', description: 'Speed + quality' },
        { id: 'high', label: 'High Quality', description: 'Maximum quality' },
    ],
}

const QUALITY_ICONS = {
    fast: Zap,
    balanced: Scale,
    high: Crown,
}

// Aspect ratio visual preview proportions (normalized to fit in a box)
const AR_PREVIEW = {
    '1:1':  { w: 24, h: 24 },
    '16:9': { w: 32, h: 18 },
    '9:16': { w: 18, h: 32 },
    '4:3':  { w: 28, h: 21 },
    '3:2':  { w: 30, h: 20 },
    '3:4':  { w: 21, h: 28 },
}

export default function ImageModal({ isOpen, onClose, onGenerate, onGeneratingStart }) {
    const [prompt, setPrompt] = useState('')
    const [model, setModel] = useState('flux')
    const [quality, setQuality] = useState('balanced')
    const [aspectRatio, setAspectRatio] = useState('1:1')
    const [style, setStyle] = useState('none')
    const [enhancePrompt, setEnhancePrompt] = useState(true)
    const [showAdvanced, setShowAdvanced] = useState(false)
    const [seed, setSeed] = useState('')
    const [negativePrompt, setNegativePrompt] = useState('')
    const [isGenerating, setIsGenerating] = useState(false)
    const [error, setError] = useState(null)
    const [config, setConfig] = useState(DEFAULT_CONFIG)

    // Fetch config from backend on mount
    useEffect(() => {
        if (isOpen) {
            fetch('http://127.0.0.1:8000/api/images/config')
                .then(r => r.json())
                .then(data => {
                    if (data.models && data.models.length > 0) {
                        setConfig(data)
                    }
                })
                .catch(err => console.warn('Could not fetch image config:', err))
        }
    }, [isOpen])

    if (!isOpen) return null

    const selectedModel = config.models.find(m => m.id === model) || config.models[0]
    const selectedAR = config.aspect_ratios.find(a => a.id === aspectRatio) || config.aspect_ratios[0]

    const handleGenerate = async () => {
        if (!prompt.trim() || isGenerating) return

        setIsGenerating(true)
        setError(null)
        if (onGeneratingStart) onGeneratingStart()

        try {
            const body = {
                prompt: prompt.trim(),
                model,
                quality,
                aspect_ratio: aspectRatio,
                style: style !== 'none' ? style : null,
                width: selectedAR.width,
                height: selectedAR.height,
                seed: seed ? parseInt(seed) : null,
                negative_prompt: negativePrompt.trim() || null,
                enhance_prompt: enhancePrompt,
            }

            const response = await fetch('http://127.0.0.1:8000/api/images/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            })

            const data = await response.json()

            if (data.status === 'success' && data.image_url) {
                // Pass result back to App.jsx for inline display
                onGenerate({
                    ...data,
                    prompt: prompt.trim(),
                })
                setPrompt('')
                setError(null)
                onClose()
            } else {
                setError(data.error_message || 'Image generation failed. Please try again.')
            }
        } catch (err) {
            console.error('Image generation error:', err)
            setError('Network error. Make sure the backend is running.')
        } finally {
            setIsGenerating(false)
        }
    }

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 10 }}
                        transition={{ duration: 0.2 }}
                        className="bg-white dark:bg-[#171717] border border-gray-200 dark:border-white/10 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl max-h-[90vh] flex flex-col"
                    >
                        {/* Header */}
                        <div className="p-5 border-b border-gray-200 dark:border-white/5 flex justify-between items-center shrink-0">
                            <div className="flex items-center gap-2.5">
                                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                                    <Sparkles className="w-4 h-4 text-white" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Generate Image</h2>
                                    <p className="text-[11px] text-gray-400 dark:text-white/40">AI-powered image generation with prompt enhancement</p>
                                </div>
                            </div>
                            <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-full transition-colors text-gray-500 dark:text-white/50 hover:text-gray-900 dark:hover:text-white">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Scrollable Content */}
                        <div className="flex-1 overflow-y-auto p-5 space-y-5 bg-white dark:bg-[#212121]">
                            {/* Prompt Input */}
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-[#c9c9c9]">Describe your image</label>
                                <textarea
                                    value={prompt}
                                    onChange={(e) => setPrompt(e.target.value)}
                                    placeholder="A cinematic photograph of a sports car on a wet street at night, dramatic lighting..."
                                    rows={3}
                                    disabled={isGenerating}
                                    className="w-full bg-gray-50 dark:bg-[#2f2f2f] border border-gray-200 dark:border-white/10 rounded-xl px-4 py-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all resize-none disabled:opacity-50"
                                />
                                {/* Enhance toggle */}
                                <label className="flex items-center gap-2.5 cursor-pointer select-none group">
                                    <div className={`relative w-9 h-5 rounded-full transition-colors ${enhancePrompt ? 'bg-indigo-500' : 'bg-gray-300 dark:bg-white/15'}`}
                                        onClick={() => setEnhancePrompt(!enhancePrompt)}
                                    >
                                        <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${enhancePrompt ? 'translate-x-4' : 'translate-x-0.5'}`} />
                                    </div>
                                    <span className="text-xs text-gray-500 dark:text-white/50 group-hover:text-gray-700 dark:group-hover:text-white/70 transition-colors">
                                        Auto-enhance prompt with AI
                                    </span>
                                    <Sparkles size={12} className={`transition-colors ${enhancePrompt ? 'text-indigo-400' : 'text-gray-300 dark:text-white/20'}`} />
                                </label>
                            </div>

                            {/* Quality Preset — Segmented Control */}
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-[#c9c9c9]">Quality</label>
                                <div className="flex gap-1.5 bg-gray-100 dark:bg-[#2f2f2f] rounded-xl p-1">
                                    {config.quality_presets.map(preset => {
                                        const Icon = QUALITY_ICONS[preset.id] || Scale
                                        const isActive = quality === preset.id
                                        return (
                                            <button
                                                key={preset.id}
                                                onClick={() => setQuality(preset.id)}
                                                disabled={isGenerating}
                                                className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                                                    isActive
                                                        ? 'bg-white dark:bg-[#424242] text-gray-900 dark:text-white shadow-sm'
                                                        : 'text-gray-500 dark:text-white/40 hover:text-gray-700 dark:hover:text-white/60'
                                                }`}
                                            >
                                                <Icon size={13} />
                                                {preset.label}
                                            </button>
                                        )
                                    })}
                                </div>
                            </div>

                            {/* Aspect Ratio — Visual Cards */}
                            <div className="space-y-2">
                                <label className="text-sm font-semibold text-gray-700 dark:text-[#c9c9c9]">Aspect Ratio</label>
                                <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                                    {config.aspect_ratios.map(ar => {
                                        const isActive = aspectRatio === ar.id
                                        const preview = AR_PREVIEW[ar.id] || { w: 24, h: 24 }
                                        return (
                                            <button
                                                key={ar.id}
                                                onClick={() => setAspectRatio(ar.id)}
                                                disabled={isGenerating}
                                                className={`flex flex-col items-center gap-1.5 py-3 px-2 rounded-xl border transition-all ${
                                                    isActive
                                                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400'
                                                        : 'border-gray-200 dark:border-white/10 text-gray-500 dark:text-white/40 hover:border-gray-300 dark:hover:border-white/20'
                                                }`}
                                            >
                                                <div className="flex items-center justify-center h-8">
                                                    <div
                                                        className={`rounded-[3px] border-2 transition-colors ${
                                                            isActive ? 'border-indigo-500 dark:border-indigo-400' : 'border-gray-300 dark:border-white/20'
                                                        }`}
                                                        style={{ width: preview.w, height: preview.h }}
                                                    />
                                                </div>
                                                <span className="text-[10px] font-medium leading-none">{ar.id}</span>
                                            </button>
                                        )
                                    })}
                                </div>
                            </div>

                            {/* Model & Style — Side by Side */}
                            <div className="grid grid-cols-2 gap-4">
                                {/* Model Selection */}
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-gray-700 dark:text-[#c9c9c9]">Model</label>
                                    <div className="relative">
                                        <select
                                            value={model}
                                            onChange={(e) => setModel(e.target.value)}
                                            disabled={isGenerating}
                                            className="w-full bg-gray-50 dark:bg-[#2f2f2f] border border-gray-200 dark:border-white/10 rounded-xl px-4 py-2.5 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all cursor-pointer appearance-none"
                                        >
                                            {config.models.map(m => (
                                                <option key={m.id} value={m.id}>{m.label}</option>
                                            ))}
                                        </select>
                                        <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400 dark:text-white/30" />
                                    </div>
                                </div>

                                {/* Style Selection */}
                                <div className="space-y-2">
                                    <label className="text-sm font-semibold text-gray-700 dark:text-[#c9c9c9]">Style</label>
                                    <div className="relative">
                                        <select
                                            value={style}
                                            onChange={(e) => setStyle(e.target.value)}
                                            disabled={isGenerating}
                                            className="w-full bg-gray-50 dark:bg-[#2f2f2f] border border-gray-200 dark:border-white/10 rounded-xl px-4 py-2.5 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all cursor-pointer appearance-none"
                                        >
                                            {config.styles.map(s => (
                                                <option key={s.id} value={s.id}>{s.label}</option>
                                            ))}
                                        </select>
                                        <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400 dark:text-white/30" />
                                    </div>
                                </div>
                            </div>

                            {/* Advanced Options — Collapsible */}
                            <div className="border border-gray-200 dark:border-white/10 rounded-xl overflow-hidden">
                                <button
                                    onClick={() => setShowAdvanced(!showAdvanced)}
                                    className="w-full flex items-center justify-between px-4 py-2.5 text-xs font-medium text-gray-500 dark:text-white/40 hover:text-gray-700 dark:hover:text-white/60 transition-colors"
                                >
                                    <span>Advanced Options</span>
                                    {showAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                </button>

                                <AnimatePresence>
                                    {showAdvanced && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            transition={{ duration: 0.2 }}
                                            className="overflow-hidden"
                                        >
                                            <div className="px-4 pb-4 space-y-3 border-t border-gray-200 dark:border-white/5 pt-3">
                                                {/* Seed */}
                                                {selectedModel.supports_seed && (
                                                    <div className="space-y-1.5">
                                                        <label className="text-xs font-medium text-gray-500 dark:text-white/40">Seed (leave blank for random)</label>
                                                        <input
                                                            type="number"
                                                            value={seed}
                                                            onChange={(e) => setSeed(e.target.value)}
                                                            placeholder="e.g. 42"
                                                            disabled={isGenerating}
                                                            className="w-full bg-gray-50 dark:bg-[#2f2f2f] border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-indigo-500/20 transition-all"
                                                        />
                                                    </div>
                                                )}

                                                {/* Negative Prompt */}
                                                {selectedModel.supports_negative_prompt && (
                                                    <div className="space-y-1.5">
                                                        <label className="text-xs font-medium text-gray-500 dark:text-white/40">Negative Prompt (what to avoid)</label>
                                                        <textarea
                                                            value={negativePrompt}
                                                            onChange={(e) => setNegativePrompt(e.target.value)}
                                                            placeholder="blurry, distorted, low quality, watermark, text..."
                                                            rows={2}
                                                            disabled={isGenerating}
                                                            className="w-full bg-gray-50 dark:bg-[#2f2f2f] border border-gray-200 dark:border-white/10 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-indigo-500/20 transition-all resize-none"
                                                        />
                                                    </div>
                                                )}

                                                {/* Dimensions info */}
                                                <div className="flex items-center justify-between text-[11px] text-gray-400 dark:text-white/30 bg-gray-50 dark:bg-black/20 rounded-lg px-3 py-2">
                                                    <span>Output dimensions</span>
                                                    <span className="font-mono">{selectedAR.width} × {selectedAR.height}</span>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>

                            {/* Error Display */}
                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, y: -5 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-xl px-4 py-3 text-sm text-red-600 dark:text-red-400 flex items-start gap-2"
                                >
                                    <span className="shrink-0 mt-0.5">⚠️</span>
                                    <span>{error}</span>
                                </motion.div>
                            )}
                        </div>

                        {/* Footer */}
                        <div className="p-4 border-t border-gray-200 dark:border-white/5 flex justify-between items-center bg-gray-50 dark:bg-[#171717] shrink-0">
                            <div className="text-[11px] text-gray-400 dark:text-white/30">
                                {selectedModel.label} · {selectedAR.width}×{selectedAR.height}
                            </div>
                            <div className="flex gap-3">
                                <button
                                    onClick={onClose}
                                    disabled={isGenerating}
                                    className="px-4 py-2 text-sm font-medium text-gray-500 dark:text-white/70 hover:text-gray-900 dark:hover:text-white transition-colors disabled:opacity-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleGenerate}
                                    disabled={!prompt.trim() || isGenerating}
                                    className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-2 shadow-lg ${
                                        prompt.trim() && !isGenerating
                                            ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-indigo-600/20'
                                            : 'bg-gray-200 dark:bg-[#2f2f2f] text-gray-400 dark:text-[#424242] cursor-not-allowed shadow-none'
                                    }`}
                                >
                                    {isGenerating ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            Generating...
                                        </>
                                    ) : (
                                        <>
                                            <Sparkles className="w-4 h-4" />
                                            Generate
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    )
}
