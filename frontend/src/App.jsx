import { useState, useEffect, useRef } from 'react'
import io from 'socket.io-client'
import {
  Plus, MessageSquare, ChevronDown, Square,
  Paperclip, Mic, ArrowUp, Menu, X, Settings, Terminal, Thermometer, Cpu, Check, Copy, User, Image, Search, Trash2, Edit2,
  Maximize2, Download, ExternalLink, AlertCircle, RefreshCw, Sparkles, Bot
} from 'lucide-react'
import Auth from './components/Auth'
import { signOutFirebase } from './firebase'
import SettingsModal from './components/SettingsModal'
import ImageModal from './components/ImageModal'
import OneeFloatingCompanion from './components/OneeFloatingCompanion'
import WelcomeGreeting from './components/WelcomeGreeting'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { Avatar } from '@bible-strong/avatar-react'
import alienDef from './assets/alien-avatar-definition.json'
import grokbotDef from './assets/grokbot-avatar-definition.json'
import strobiDef from './assets/strobi-avatar-definition.json'
import oneeDef from './assets/onee-avatar-definition.json'

// Connect to the Python Backend
const socket = io('http://127.0.0.1:8000', {
  transports: ['websocket', 'polling']
})

// Official Bible Strong Avatar Presets
const AVATAR_PRESETS = {
  alien: { name: 'Alien (Neon)', def: alienDef, desc: 'Neon Alien Companion (Reel)' },
  grokbot: { name: 'Grok bot', def: grokbotDef, desc: 'Dark Sphere' },
  strobi: { name: 'Strobi', def: strobiDef, desc: 'Studio Default (Blue)' },
  onee: { name: 'Onee', def: oneeDef, desc: 'Cone Avatar' },
}

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [temperature, setTemperature] = useState(0.7)
  const [availableModels, setAvailableModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('gemini-2.5-flash')
  const [isListening, setIsListening] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [isImageModalOpen, setIsImageModalOpen] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [newChatKey, setNewChatKey] = useState(1)
  const [theme, setTheme] = useState('system') // 'light', 'dark', 'system'
  const [voice, setVoice] = useState('male') // 'male', 'female'
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('alias_user')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    try {
      return !!localStorage.getItem('alias_user')
    } catch {
      return false
    }
  })
  const userFirstName = (user?.given_name || user?.name || user?.displayName || '').trim().split(' ')[0]

  // Avatar Presets & Emotion State
  const [avatarPreset, setAvatarPreset] = useState(() => localStorage.getItem('alias_avatar_preset') || 'alien')
  const activeAvatarDef = AVATAR_PRESETS[avatarPreset]?.def || alienDef
  const [companionSpeech, setCompanionSpeech] = useState('')
  const companionSpeechTimeoutRef = useRef(null)
  const [settingsInitialTab, setSettingsInitialTab] = useState('general')

  // Companion Configuration (Size, Alignment with Text Box, and Visuals)
  const [companionConfig, setCompanionConfig] = useState(() => {
    try {
      const saved = localStorage.getItem('alias_companion_config')
      if (saved) return JSON.parse(saved)
    } catch {
      // ignore
    }
    return {
      enabled: true,
      size: 78,
      positionMode: 'docked', // 'docked' (alongside text box) or 'floating' (bottom-right corner)
      showSpeechBubble: true,
      enableGlow: true,
      customExpression: null
    }
  })

  const updateCompanionConfig = (updates) => {
    setCompanionConfig(prev => {
      const next = { ...prev, ...updates }
      localStorage.setItem('alias_companion_config', JSON.stringify(next))
      return next
    })
  }

  const handleSelectPreset = (key) => {
    setAvatarPreset(key)
    localStorage.setItem('alias_avatar_preset', key)
    triggerAvatarState('happy', 2500)
  }

  // Avatar Lifecycle & Emotions
  const [avatarAnimation, setAvatarAnimation] = useState('idle')
  const [avatarExpression, setAvatarExpression] = useState('neutral')
  const [isAvatarStudioOpen, setIsAvatarStudioOpen] = useState(false)
  const avatarTimeoutRef = useRef(null)
  const lastActivityRef = useRef(Date.now())

  // Dynamic Expression & Emotion Controller
  const triggerAvatarMood = (expression = 'neutral', duration = 0, animation = 'idle') => {
    // If user locked a specific fixed expression in settings, preserve user preference
    if (companionConfig.customExpression) return

    setAvatarExpression(expression)
    setAvatarAnimation(animation || 'idle')

    if (avatarTimeoutRef.current) {
      clearTimeout(avatarTimeoutRef.current)
      avatarTimeoutRef.current = null
    }

    if (duration > 0) {
      avatarTimeoutRef.current = setTimeout(() => {
        // Return smoothly to Neutral: Calm, composed, and balanced
        setAvatarExpression('neutral')
        setAvatarAnimation('idle')
      }, duration)
    }
  }

  // Backward-compatible triggerAvatarState mapped to user's exact specification
  const triggerAvatarState = (state, duration = 0) => {
    switch (state) {
      case 'thinking':
        // Curious: Inquisitive head tilt (while processing question)
        triggerAvatarMood('curious-left', duration, 'thinking')
        break
      case 'working':
        // Focused: Deep concentration and attentive eyes
        triggerAvatarMood('attentive-left', duration, 'working')
        break
      case 'listening':
        triggerAvatarMood('attentive-left', duration, 'listening')
        break
      case 'celebrate':
        // Joyful: Cheerful, smiling, and enthusiastic
        triggerAvatarMood('joyful-wide', duration || 4500, 'celebrate')
        break
      case 'happy':
        // Joyful
        triggerAvatarMood('joyful-wide', duration || 4000, 'happy')
        break
      case 'confused':
      case 'error':
        // Surprised: Wide, alert eyes (when some error occurs)
        triggerAvatarMood('surprised-left', duration || 4500, 'confused')
        break
      case 'playful':
        // Playful: Lively sideways glance (when hi/hey or output generated)
        triggerAvatarMood('playful-right', duration || 4000, 'happy')
        break
      case 'skeptical':
        // Skeptical: Analytical raised-eye tilt (inquiries, doubts, warnings)
        triggerAvatarMood('skeptical-left', duration || 4000, 'thinking')
        break
      case 'shy':
        // Gentle / Shy: Soft downward gaze (politeness, goodnight, apologies)
        triggerAvatarMood('shy-downward', duration || 4000, 'shy')
        break
      case 'sleeping':
      case 'drowsy':
      case 'bored':
        // Sleepy: Chill, resting eyes (when there is no work)
        triggerAvatarMood('sleepy-squint', duration, 'sleeping')
        break
      case 'idle':
      default:
        // Neutral: Calm, composed, and balanced (normal chat)
        triggerAvatarMood('neutral', duration, 'idle')
        break
    }
  }

  // Detect user question intent to set conversational mood immediately
  const detectInputMood = (rawText) => {
    if (!rawText) return null
    const text = rawText.trim().toLowerCase()

    // 1. Playful: Lively sideways glance (when user says hi, hey, greetings)
    const greetings = ['hi', 'hey', 'hello', 'hola', 'sup', "what's up", 'yo', 'good morning', 'good afternoon', 'good evening', 'howdy']
    if (greetings.some(g => text === g || text.startsWith(g + ' ') || text.startsWith(g + '!') || text.startsWith(g + ','))) {
      return { mood: 'playful-right', anim: 'happy', speech: 'Hey there! Ready to assist you.' }
    }

    // 2. Gentle / Shy: Soft downward gaze (polite goodbyes, apologies, compliments)
    const shyTriggers = ['bye', 'goodbye', 'good night', 'gn', 'see you', 'take care', 'cya', 'sorry', 'apologize', 'excuse me', 'love you', 'cute', 'adorable', 'sweet']
    if (shyTriggers.some(t => text.includes(t))) {
      return { mood: 'shy-downward', anim: 'shy', speech: null }
    }

    // 3. Joyful: Cheerful, smiling, enthusiastic (praises, compliments, gratitude)
    const praiseTriggers = ['thank', 'thanks', 'thx', 'great job', 'awesome', 'wonderful', 'perfect', 'amazing', 'well done', 'you are the best', 'superb', 'brilliant', 'good work']
    if (praiseTriggers.some(p => text.includes(p))) {
      return { mood: 'joyful-wide', anim: 'celebrate', speech: 'My pleasure! Glad I could help.' }
    }

    // 4. Skeptical: Analytical raised-eye tilt (doubts, questioning, 'why', 'are you sure')
    const skepticalTriggers = ['are you sure', 'really?', 'really ?', 'why would', 'can you actually', 'how come', 'prove it', 'is that true', 'doubt', 'are you certain', 'explain yourself']
    if (skepticalTriggers.some(s => text.includes(s))) {
      return { mood: 'skeptical-left', anim: 'thinking', speech: 'Let me analyze that critically...' }
    }

    // 5. Focused: Deep concentration and attentive eyes (image creation requests)
    if (text.startsWith('generate image') || text.startsWith('/image') || text.includes('draw a') || text.includes('generate a picture')) {
      return { mood: 'attentive-left', anim: 'working', speech: 'Focusing on your image creation...' }
    }

    // Default: Curious: Inquisitive head tilt while processing the question
    return { mood: 'curious-left', anim: 'thinking', speech: 'Let me think...' }
  }

  // Inactivity & wake-up lifecycle manager (Sleepy when there is no work)
  useEffect(() => {
    const handleUserActivity = () => {
      lastActivityRef.current = Date.now()
      if (!companionConfig.customExpression && (avatarExpression === 'sleepy-squint' || avatarAnimation === 'sleeping')) {
        // Wake up gently back to Neutral: Calm, composed, and balanced
        if (avatarTimeoutRef.current) clearTimeout(avatarTimeoutRef.current)
        triggerAvatarMood('neutral', 0, 'idle')
      }
    }

    window.addEventListener('mousemove', handleUserActivity, { passive: true })
    window.addEventListener('keydown', handleUserActivity, { passive: true })
    window.addEventListener('click', handleUserActivity, { passive: true })
    window.addEventListener('scroll', handleUserActivity, { passive: true })

    const interval = setInterval(() => {
      if (companionConfig.customExpression) return
      const elapsed = Date.now() - lastActivityRef.current
      if (['listening', 'thinking', 'working'].includes(avatarAnimation)) {
        return
      }
      if (elapsed > 25000) {
        // Sleepy: Chill resting eyes when there is no work
        setAvatarExpression('sleepy-squint')
        setAvatarAnimation('sleeping')
      }
    }, 5000)

    return () => {
      window.removeEventListener('mousemove', handleUserActivity)
      window.removeEventListener('keydown', handleUserActivity)
      window.removeEventListener('click', handleUserActivity)
      window.removeEventListener('scroll', handleUserActivity)
      clearInterval(interval)
    }
  }, [companionConfig.customExpression, avatarExpression, avatarAnimation])

  // Chat History & Memories State
  const [conversations, setConversations] = useState([])
  const [currentConversationId, setCurrentConversationId] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [memories, setMemories] = useState([])
  const [editingId, setEditingId] = useState(null)
  const [editingTitle, setEditingTitle] = useState('')

  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    socket.on('response', (data) => {
      if (data.type === 'error') {
        addMessage('system', data.data)
        triggerAvatarState('confused', 4000)
        setCompanionSpeech(data.data || 'Something went wrong.')
      }
    })

    socket.on('avatar_state', (data) => {
      if (data?.state) {
        if (['celebrate', 'happy', 'laughing', 'confused', 'playful', 'surprised', 'excited'].includes(data.state)) {
          triggerAvatarState(data.state, 4000)
        } else {
          triggerAvatarState(data.state)
        }
      }
      if (data?.text) {
        setCompanionSpeech(data.text)
      }
    })

    socket.on('chat_start', (data) => {
      triggerAvatarState('thinking')
      setCompanionSpeech('Let me think...')
      setMessages(prev => [...prev, { role: 'ai', text: '', isStreaming: true }])
    })

    socket.on('chat_chunk', (data) => {
      triggerAvatarState('working')
      setCompanionSpeech(prev => {
        if (!prev || prev === 'Let me think...') return data.chunk
        return prev + data.chunk
      })
      setMessages(prev => {
        const updated = [...prev]
        if (updated.length > 0 && updated[updated.length - 1].role === 'ai') {
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            text: updated[updated.length - 1].text + data.chunk
          }
        }
        return updated
      })
    })

    socket.on('chat_end', (data) => {
      if (companionSpeechTimeoutRef.current) clearTimeout(companionSpeechTimeoutRef.current)
      companionSpeechTimeoutRef.current = setTimeout(() => {
        setCompanionSpeech('')
      }, 7000)
      setMessages(prev => {
        const updated = [...prev]
        if (updated.length > 0 && updated[updated.length - 1].role === 'ai') {
          const finalMsg = updated[updated.length - 1].text.toLowerCase()
          if (finalMsg.includes('error') || finalMsg.includes('failed') || finalMsg.includes('exception')) {
            // Surprised: Wide alert eyes when some error occurs
            triggerAvatarMood('surprised-left', 5000, 'confused')
          } else if (finalMsg.includes('document') || finalMsg.includes('pdf') || finalMsg.includes('word') || finalMsg.includes('generated image') || finalMsg.includes('launched') || finalMsg.includes('created')) {
            // Joyful: Cheerful smiling on creation / accomplishments
            triggerAvatarMood('joyful-wide', 4500, 'celebrate')
          } else if (finalMsg.includes('sorry') || finalMsg.includes('apologize')) {
            // Gentle / Shy: Soft downward gaze on apology
            triggerAvatarMood('shy-downward', 4500, 'shy')
          } else {
            // Playful: Lively sideways glance when output is generated!
            triggerAvatarMood('playful-right', 4500, 'happy')
          }
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            isStreaming: false
          }
        }
        return updated
      })
    })

    socket.on('status', (data) => {
      const listening = data.status === 'listening'
      setIsListening(listening)
      if (listening) {
        triggerAvatarState('listening')
        setCompanionSpeech("I'm listening...")
      } else {
        triggerAvatarState('idle')
        setCompanionSpeech('')
      }
    })

    socket.on('recognized_text', (data) => {
      addMessage('user', data.text)
    })

    socket.on('available_models', (data) => {
      console.log("Received models:", data.models)
      setAvailableModels(data.models)
      if (data.models.length > 0 && !data.models.includes(selectedModel)) {
        setSelectedModel(data.models[0])
      }
    })

    socket.on('conversations_list', (data) => {
      setConversations(data.conversations || [])
    })

    socket.on('conversation_history', (data) => {
      const history = data.messages || []
      setMessages(history.map(m => ({
        role: m.role,
        text: m.content
      })))
    })

    socket.on('conversation_started', (data) => {
      setCurrentConversationId(data.conversation_id)
      if (user?.email) {
        socket.emit('get_conversations', { email: user.email })
      }
    })

    socket.on('conversation_renamed', (data) => {
      setConversations(prev => prev.map(c => c.id === data.conversation_id ? { ...c, title: data.title } : c))
    })

    socket.on('conversation_deleted', (data) => {
      setConversations(prev => prev.filter(c => c.id !== data.conversation_id))
      setCurrentConversationId(prev => {
        if (prev === data.conversation_id) {
          setMessages([])
          setNewChatKey(k => k + 1)
          return null
        }
        return prev
      })
    })

    socket.on('memories_list', (data) => {
      setMemories(data.memories || [])
    })

    // Explicitly request models in case we missed the connect event
    socket.emit('get_models')

    return () => {
      socket.off('response')
      socket.off('avatar_state')
      socket.off('chat_start')
      socket.off('chat_chunk')
      socket.off('chat_end')
      socket.off('status')
      socket.off('recognized_text')
      socket.off('available_models')
      socket.off('conversations_list')
      socket.off('conversation_history')
      socket.off('conversation_started')
      socket.off('conversation_renamed')
      socket.off('conversation_deleted')
      socket.off('memories_list')
    }
  }, [selectedModel, user])

  useEffect(() => {
    const savedUser = localStorage.getItem('alias_user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
      setIsAuthenticated(true)
    }
  }, [])

  useEffect(() => {
    if (isAuthenticated && user?.email) {
      socket.emit('get_conversations', { email: user.email })
      socket.emit('get_memories', { email: user.email })
    }
  }, [isAuthenticated, user])

  // ... (rest of the file)

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    triggerAvatarState('working')
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://127.0.0.1:8000/upload', {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      if (data.status === 'success') {
        addMessage('system', `File uploaded: ${file.name}`)
        triggerAvatarState('celebrate', 3500)
        console.log("Upload success:", data)
      } else {
        addMessage('system', `Upload failed: ${data.error}`)
        triggerAvatarState('confused', 3500)
      }
    } catch (error) {
      console.error('Upload Error:', error)
      addMessage('system', 'Upload failed (Network Error)')
      triggerAvatarState('confused', 3500)
    }
  }



  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Theme Logic
  useEffect(() => {
    const root = window.document.documentElement
    root.classList.remove('dark', 'light')

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      root.classList.add(systemTheme)
    } else {
      root.classList.add(theme)
    }
  }, [theme])

  // Voice Change Logic
  useEffect(() => {
    socket.emit('change_voice', { voice: voice })
  }, [voice])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  const addMessage = (role, text) => {
    setMessages(prev => [...prev, { role, text }])
  }

  const sendMessage = () => {
    if (!input.trim()) return
    const textToSend = input
    addMessage('user', textToSend)

    const detected = detectInputMood(textToSend)
    if (detected) {
      triggerAvatarMood(detected.mood, 0, detected.anim)
      if (detected.speech) {
        setCompanionSpeech(detected.speech)
      }
    } else {
      // Curious: Inquisitive head tilt while processing the question
      triggerAvatarMood('curious-left', 0, 'thinking')
      setCompanionSpeech('Let me think...')
    }

    socket.emit('process_text', {
      text: textToSend,
      temperature: parseFloat(temperature),
      model: selectedModel,
      username: user ? user.name : 'Guest',
      email: user ? user.email : 'guest@alias.com',
      conversation_id: currentConversationId
    })
    setInput('')
  }

  const handleImageGenerate = (result) => {
    // Add user message showing what was requested
    addMessage('user', `Generate image: "${result.prompt || result.original_prompt}"`)

    if (result.status === 'success' && result.image_url) {
      // Playful / Joyful lively output generated
      triggerAvatarMood('playful-right', 5000, 'celebrate')
      // Build a rich AI response with the generated image
      const parts = [
        `Here's your generated image:\n`,
        `![Generated Image](${result.image_url})\n`,
        `**Model:** ${result.model} · **Size:** ${result.width}×${result.height} · **Provider:** ${result.provider}`,
      ]
      if (result.enhanced_prompt && result.enhanced_prompt !== result.original_prompt) {
        parts.push(`\n\n*Enhanced prompt: "${result.enhanced_prompt.substring(0, 150)}${result.enhanced_prompt.length > 150 ? '...' : ''}"*`)
      }
      if (result.generation_time) {
        parts.push(`\n*Generated in ${result.generation_time}s*`)
      }
      addMessage('ai', parts.join('\n'))
    } else {
      // Surprised: Wide alert eyes when some error occurs
      triggerAvatarMood('surprised-left', 5000, 'confused')
      addMessage('ai', `Sorry, image generation failed: ${result.error_message || 'Unknown error. Please try again.'}`)
    }
  }

  const startNewChat = () => {
    setMessages([])
    setInput('')
    setCurrentConversationId(null)
    setNewChatKey(prev => prev + 1)
  }

  const selectConversation = (id) => {
    setCurrentConversationId(id)
    socket.emit('get_conversation', { conversation_id: id })
  }

  const handleRenameConversation = (id, newTitle) => {
    socket.emit('rename_conversation', { conversation_id: id, title: newTitle })
  }

  const handleDeleteConversation = (id, e) => {
    e.stopPropagation()
    socket.emit('delete_conversation', { conversation_id: id })
  }

  const handleDeleteMemory = (memoryId) => {
    if (user?.email) {
      socket.emit('delete_memory', { email: user.email, memory_id: memoryId })
    }
  }

  const startEditing = (id, title) => {
    setEditingId(id)
    setEditingTitle(title)
  }

  const saveTitle = (id) => {
    if (editingTitle.trim()) {
      handleRenameConversation(id, editingTitle.trim())
    }
    setEditingId(null)
  }

  const cancelEditing = () => {
    setEditingId(null)
  }

  const toggleVoice = () => {
    socket.emit('start_listening')
  }

  const stopTTS = () => {
    socket.emit('stop_tts')
  }

  // Custom Code Block Renderer
  const CodeBlock = ({ node, inline, className, children, ...props }) => {
    const match = /language-(\w+)/.exec(className || '')
    const language = match ? match[1] : ''
    const [copied, setCopied] = useState(false)

    const handleCopy = () => {
      navigator.clipboard.writeText(String(children).replace(/\n$/, ''))
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }

    if (!inline && match) {
      return (
        <div className="rounded-lg overflow-hidden my-4 border border-gray-700/50 shadow-sm">
          <div className="flex items-center justify-between px-4 py-2 bg-gray-800 text-gray-200 text-xs border-b border-gray-700">
            <span className="font-mono uppercase text-white/70">{language}</span>
            <button onClick={handleCopy} className="flex items-center gap-1.5 hover:text-white transition-colors">
              {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <SyntaxHighlighter
            style={vscDarkPlus}
            language={language}
            PreTag="div"
            customStyle={{ margin: 0, padding: '1rem', background: '#1e1e1e' }}
            {...props}
          >
            {String(children).replace(/\n$/, '')}
          </SyntaxHighlighter>
        </div>
      )
    }

    return (
      <code className={`${className} bg-black/10 dark:bg-white/10 px-1 py-0.5 rounded font-mono text-[0.9em]`} {...props}>
        {children}
      </code>
    )
  }

  // Custom Markdown Image Renderer with loading, fallback, lightbox and actions
  const MarkdownImage = ({ src, alt, ...props }) => {
    const [status, setStatus] = useState('loading') // 'loading' | 'loaded' | 'error'
    const [currentSrc, setCurrentSrc] = useState(src)
    const [retryCount, setRetryCount] = useState(0)
    const [isZoomed, setIsZoomed] = useState(false)

    // Normalize image src
    useEffect(() => {
      if (!src) return
      let normalized = src
      if (normalized.startsWith('/images/')) {
        normalized = `http://127.0.0.1:8000${normalized}`
      }
      setCurrentSrc(normalized)
      setStatus('loading')
    }, [src, retryCount])

    const handleError = () => {
      // If 127.0.0.1 failed, try localhost as backup
      if (currentSrc.includes('127.0.0.1:8000')) {
        setCurrentSrc(currentSrc.replace('127.0.0.1:8000', 'localhost:8000'))
      } else if (currentSrc.includes('localhost:8000')) {
        setCurrentSrc(currentSrc.replace('http://localhost:8000', ''))
      } else {
        setStatus('error')
      }
    }

    const handleDownload = async (e) => {
      e.stopPropagation()
      try {
        const response = await fetch(currentSrc)
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = currentSrc.split('/').pop() || 'alias-generated-image.jpg'
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      } catch (err) {
        window.open(currentSrc, '_blank')
      }
    }

    return (
      <div className="my-4 group relative inline-block max-w-full not-prose">
        <div className="relative rounded-2xl overflow-hidden border border-gray-200 dark:border-white/10 shadow-lg bg-black/5 dark:bg-black/30 backdrop-blur-sm">
          {status === 'loading' && (
            <div className="w-full min-w-[280px] h-64 flex flex-col items-center justify-center bg-gray-100 dark:bg-[#1a1a1a] animate-pulse">
              <RefreshCw className="animate-spin text-gray-400 mb-2" size={24} />
              <span className="text-xs text-gray-500">Loading generated image...</span>
            </div>
          )}

          {status === 'error' ? (
            <div className="p-6 flex flex-col items-center justify-center text-center bg-red-500/5 dark:bg-red-500/10 border border-red-500/20 rounded-2xl min-w-[280px]">
              <AlertCircle className="text-red-400 mb-2" size={28} />
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">Unable to load image</p>
              <p className="text-xs text-gray-500 mb-3 truncate max-w-xs">{alt || currentSrc.split('/').pop()}</p>
              <div className="flex gap-2">
                <button
                  onClick={() => setRetryCount(c => c + 1)}
                  className="px-3 py-1.5 text-xs bg-gray-200 dark:bg-white/10 hover:bg-gray-300 dark:hover:bg-white/20 rounded-lg transition-colors flex items-center gap-1.5"
                >
                  <RefreshCw size={12} /> Retry
                </button>
                <a
                  href={currentSrc}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors flex items-center gap-1.5"
                >
                  <ExternalLink size={12} /> Open Direct
                </a>
              </div>
            </div>
          ) : (
            <img
              src={currentSrc}
              alt={alt || "Generated Image"}
              onLoad={() => setStatus('loaded')}
              onError={handleError}
              onClick={() => setIsZoomed(true)}
              className={`max-w-full max-h-[500px] object-contain rounded-2xl cursor-zoom-in transition-all duration-300 ${status === 'loading' ? 'hidden' : 'block hover:scale-[1.01]'}`}
              {...props}
            />
          )}

          {status === 'loaded' && (
            <div className="absolute top-3 right-3 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 backdrop-blur-md rounded-xl p-1 shadow-md">
              <button
                onClick={() => setIsZoomed(true)}
                title="Expand"
                className="p-1.5 text-white/80 hover:text-white hover:bg-white/20 rounded-lg transition-colors"
              >
                <Maximize2 size={14} />
              </button>
              <button
                onClick={handleDownload}
                title="Download"
                className="p-1.5 text-white/80 hover:text-white hover:bg-white/20 rounded-lg transition-colors"
              >
                <Download size={14} />
              </button>
            </div>
          )}
        </div>

        {/* Lightbox / Zoom Modal */}
        {isZoomed && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in"
            onClick={() => setIsZoomed(false)}
          >
            <div className="relative max-w-5xl max-h-[90vh] flex flex-col items-center" onClick={e => e.stopPropagation()}>
              <div className="absolute top-2 right-2 flex items-center gap-2 z-10">
                <button
                  onClick={handleDownload}
                  className="p-2 bg-black/60 hover:bg-black/80 text-white rounded-full transition-colors"
                  title="Download"
                >
                  <Download size={18} />
                </button>
                <button
                  onClick={() => setIsZoomed(false)}
                  className="p-2 bg-black/60 hover:bg-black/80 text-white rounded-full transition-colors"
                  title="Close"
                >
                  <X size={18} />
                </button>
              </div>
              <img
                src={currentSrc}
                alt={alt || "Zoomed Image"}
                className="max-w-full max-h-[85vh] rounded-xl object-contain shadow-2xl"
              />
              <p className="mt-3 text-sm text-white/70">{alt || "Generated Image"}</p>
            </div>
          </div>
        )}
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Auth onLoginSuccess={(userData) => {
      setIsAuthenticated(true);
      setUser(userData);
      localStorage.setItem('alias_user', JSON.stringify(userData));
    }} />
  }

  return (
    <div className="flex h-screen bg-white dark:bg-[#212121] text-gray-900 dark:text-[#ececec] font-sans overflow-hidden transition-colors duration-200">

      {/* Sidebar */}
      <div className={`${isSidebarOpen ? 'w-[260px]' : 'w-0'} bg-gray-50 dark:bg-[#171717] flex flex-col transition-all duration-300 overflow-hidden shrink-0 border-r border-gray-200 dark:border-white/5 h-full`}>
        <div className="p-3 flex items-center justify-between group">
          <button onClick={startNewChat} className="flex-1 flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-gray-200 dark:hover:bg-[#212121] transition-colors text-sm font-medium">
            <div className="h-6 w-6 rounded-full flex items-center justify-center overflow-hidden">
              <img src="/logo.png" alt="ALIAS" className="w-full h-full object-cover" />
            </div>
            <span>ALIAS</span>
          </button>
          <button onClick={() => setIsSidebarOpen(false)} className="p-2 text-gray-500 dark:text-white/50 hover:text-black dark:hover:text-white lg:hidden">
            <X size={20} />
          </button>
        </div>

        <div className="px-3 py-2 space-y-4 shrink-0">
          <button onClick={startNewChat} className="w-full flex items-center justify-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors bg-gray-200 dark:bg-[#212121] text-gray-900 dark:text-white hover:opacity-90">
            <Plus size={18} />
            <span>New chat</span>
          </button>

          {/* Model Selection */}
          <div className="space-y-1.5 px-1">
            <div className="flex items-center gap-2 text-[10px] font-semibold text-gray-400 dark:text-white/30 uppercase tracking-wider px-1">
              <Cpu size={12} />
              <span>Intelligence</span>
            </div>
            <div className="relative">
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={availableModels.length === 0}
                className="w-full bg-gray-100 dark:bg-[#2f2f2f] text-gray-900 dark:text-white text-xs rounded-md px-3 py-2 appearance-none cursor-pointer focus:outline-none focus:ring-1 focus:ring-black/5 dark:focus:ring-white/10"
              >
                {availableModels.length > 0 ? (
                  availableModels.map(model => (
                    <option key={model} value={model}>{model}</option>
                  ))
                ) : (
                  <option>No API Keys Found</option>
                )}
              </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400 dark:text-white/50">
                <ChevronDown size={12} />
              </div>
            </div>
          </div>

          {/* Temperature Controls */}
          <div className="space-y-1.5 px-1">
            <div className="flex items-center justify-between text-[10px] font-semibold text-gray-400 dark:text-white/30 uppercase tracking-wider px-1">
              <div className="flex items-center gap-2">
                <Thermometer size={12} />
                <span>Creativity</span>
              </div>
              <span>{temperature}</span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(e.target.value)}
              className="w-full h-1 bg-gray-300 dark:bg-white/10 rounded-lg appearance-none cursor-pointer accent-red-600 dark:accent-red-500"
            />
          </div>

          {/* Search History */}
          <div className="relative px-1">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 dark:text-white/30">
              <Search size={13} />
            </span>
            <input
              type="text"
              placeholder="Search history..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-gray-100 dark:bg-[#212121]/50 border border-gray-200 dark:border-white/5 rounded-lg text-xs outline-none text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-white/30 focus:border-gray-300 dark:focus:border-white/15 transition-all"
            />
          </div>
        </div>

        {/* Chat History List */}
        <div className="flex-1 min-h-0 px-3 py-2 flex flex-col space-y-2">
          <div className="text-[10px] font-semibold text-gray-400 dark:text-white/30 px-1 uppercase tracking-wider">
            Recent chats
          </div>
          <div className="flex-1 overflow-y-auto space-y-0.5 pr-1">
            {(() => {
              const filtered = conversations.filter(c =>
                c.title.toLowerCase().includes(searchTerm.toLowerCase())
              );
              if (filtered.length === 0) {
                return (
                  <div className="text-center py-4 text-xs text-gray-400 dark:text-white/20">
                    {searchTerm ? 'No matches' : 'No previous chats'}
                  </div>
                );
              }
              return filtered.map(conv => {
                const isActive = currentConversationId === conv.id;
                const isEditing = editingId === conv.id;
                return (
                  <div
                    key={conv.id}
                    onClick={() => !isEditing && selectConversation(conv.id)}
                    className={`group w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg text-xs transition-all cursor-pointer ${
                      isActive
                        ? 'bg-gray-200 dark:bg-[#2f2f2f] text-gray-950 dark:text-white font-medium shadow-sm'
                        : 'text-gray-600 dark:text-white/60 hover:bg-gray-200/50 dark:hover:bg-[#212121]/50 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 flex-1 min-w-0">
                      <MessageSquare size={13} className="shrink-0" />
                      {isEditing ? (
                        <input
                          type="text"
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              saveTitle(conv.id)
                            } else if (e.key === 'Escape') {
                              cancelEditing()
                            }
                          }}
                          onBlur={() => saveTitle(conv.id)}
                          autoFocus
                          className="w-full bg-transparent outline-none border-b border-gray-400 dark:border-white/30 py-0.5 text-gray-900 dark:text-white"
                          onClick={(e) => e.stopPropagation()}
                        />
                      ) : (
                        <span className="truncate flex-1 font-light leading-none py-0.5">{conv.title}</span>
                      )}
                    </div>

                    {!isEditing && (
                      <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startEditing(conv.id, conv.title);
                          }}
                          className="p-1 hover:text-gray-950 dark:hover:text-white rounded transition-colors"
                          title="Rename chat"
                        >
                          <Edit2 size={11} />
                        </button>
                        <button
                          onClick={(e) => handleDeleteConversation(conv.id, e)}
                          className="p-1 hover:text-red-500 rounded transition-colors"
                          title="Delete chat"
                        >
                          <Trash2 size={11} />
                        </button>
                      </div>
                    )}
                  </div>
                );
              });
            })()}
          </div>
        </div>

        <div className="p-3 border-t border-gray-200 dark:border-white/5 space-y-2">
          {user && (
            <div className="flex items-center gap-3 px-3 py-2 rounded-xl bg-gray-100 dark:bg-white/5 border border-gray-200 dark:border-white/10 mb-1">
              {user.picture ? (
                <img src={user.picture} alt={user.name || 'User'} className="w-8 h-8 rounded-full object-cover ring-1 ring-white/20" />
              ) : (
                <div className="w-8 h-8 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-semibold text-xs border border-blue-500/30">
                  {user.name ? user.name[0].toUpperCase() : 'U'}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold text-gray-800 dark:text-white truncate flex items-center gap-1.5">
                  <span className="truncate">{user.name || 'User'}</span>
                  {user.provider === 'google' && (
                    <span className="text-[10px] px-1.5 py-0.2 bg-blue-500/20 text-blue-400 rounded-full font-normal">Google</span>
                  )}
                </div>
                <div className="text-[11px] text-gray-500 dark:text-white/40 truncate">{user.email}</div>
              </div>
            </div>
          )}
          <button onClick={() => setIsSettingsOpen(true)} className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-200 dark:hover:bg-[#212121] transition-colors">
            <Settings size={18} className="text-gray-500 dark:text-white/70" />
            <div className="flex-1 text-left text-sm font-medium text-gray-700 dark:text-white">
              Settings
            </div>
          </button>
          <button onClick={() => { 
            signOutFirebase();
            setIsAuthenticated(false); 
            setUser(null); 
            localStorage.removeItem('alias_user'); 
          }} className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-200 dark:hover:bg-[#212121] transition-colors">
            <User size={18} className="text-gray-500 dark:text-white/70" />
            <div className="flex-1 text-left text-sm font-medium text-red-500">
              Sign Out
            </div>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col bg-white dark:bg-[#212121] relative min-w-0 transition-colors duration-200">

        {/* Top Bar */}
        <header className="flex items-center p-4 sticky top-0 z-10 bg-white/60 dark:bg-[#212121]/60 backdrop-blur-md">
          {!isSidebarOpen && (
            <button onClick={() => setIsSidebarOpen(true)} className="p-2 hover:bg-gray-100 dark:hover:bg-[#2f2f2f] rounded-lg mr-4 text-gray-700 dark:text-white">
              <Menu size={20} />
            </button>
          )}
          <button className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white/90 hover:bg-gray-100 dark:hover:bg-[#2f2f2f] px-3 py-1.5 rounded-lg transition-colors">
            <span>ALIAS</span>
            <span className="bg-gray-200 dark:bg-white/10 text-xs px-1.5 py-0.5 rounded text-gray-500 dark:text-white/50">{user ? user.name : 'Core'}</span>
          </button>
        </header>

        {/* Chat Area */}
        <main className="flex-1 overflow-y-auto">
          {messages.length === 0 && !currentConversationId ? (
            <div className="h-full flex flex-col items-center justify-center px-4 pb-20 select-none">
              <WelcomeGreeting
                key={newChatKey}
                name={userFirstName}
              />
            </div>
          ) : (
            <div className="max-w-3xl mx-auto pt-10 px-4 pb-32 space-y-6">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'ai' && (
                    <div className="w-8 h-8 rounded-full bg-black dark:bg-white flex items-center justify-center shrink-0 mt-1 overflow-hidden shadow-sm">
                      <img src="/logo.png" alt="AI" className="w-full h-full object-cover" />
                    </div>
                  )}
                  <div className={`leading-relaxed max-w-[85%] ${msg.role === 'user' ? 'bg-gray-100 dark:bg-[#2f2f2f] px-5 py-3 rounded-3xl rounded-tr-sm text-gray-900 dark:text-white' : 'text-gray-900 dark:text-[#ececec] w-full'}`}>
                    {msg.role === 'ai' ? (
                      <div className="prose dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:p-0 prose-pre:bg-transparent">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          rehypePlugins={[rehypeRaw]}
                          components={{
                            code: CodeBlock,
                            img: MarkdownImage
                          }}
                        >
                          {msg.text}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      msg.text
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </main>

        {/* Input Area */}
        <div className="w-full px-4 pb-6 pt-2">
          <div className="max-w-3xl mx-auto relative">
            <div className="flex items-center gap-3">
              <div className="flex-1 min-w-0 bg-gray-50 dark:bg-[#2f2f2f] rounded-[26px] p-2 flex flex-col relative focus-within:ring-1 focus-within:ring-black/10 dark:focus-within:ring-white/20 transition-shadow">

                {/* Input Top Actions */}
                <div className="flex items-end gap-2 px-2">
                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onFocus={() => {
                      if (['idle', 'bored', 'drowsy'].includes(avatarAnimation)) {
                        triggerAvatarState('listening');
                      }
                    }}
                    onBlur={() => {
                      if (avatarAnimation === 'listening') {
                        triggerAvatarState('idle');
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                      }
                    }}
                    placeholder="Message ALIAS..."
                    className="flex-1 bg-transparent border-none outline-none text-gray-900 dark:text-white resize-none max-h-[200px] py-3.5 px-1 min-h-[52px] placeholder:text-gray-400 dark:placeholder:text-white/30"
                    rows={1}
                  />
                </div>

                {/* Input Bottom Actions */}
                <div className="flex justify-between items-center px-2 pb-1">
                  <div className="flex gap-2">
                    <button onClick={() => fileInputRef.current?.click()} className="p-2 text-gray-400 dark:text-white/50 hover:text-gray-900 dark:hover:text-white transition-colors" title="Attach File">
                      <Paperclip size={18} />
                    </button>
                    <button onClick={() => setIsImageModalOpen(true)} className="p-2 text-gray-400 dark:text-white/50 hover:text-gray-900 dark:hover:text-white transition-colors" title="Generate AI Image">
                      <Image size={18} />
                    </button>
                    <input
                      type="file"
                      ref={fileInputRef}
                      className="hidden"
                      onChange={handleFileUpload}
                    />
                  </div>

                  <div className="flex gap-2">
                    <button onClick={toggleVoice} className={`p-2 rounded-full transition-all ${isListening ? 'bg-black dark:bg-white text-white dark:text-black animate-pulse' : 'text-gray-400 dark:text-white/80 hover:bg-black/5 dark:hover:bg-black/20'}`}>
                      <Mic size={20} />
                    </button>
                    <button onClick={stopTTS} className="p-2 rounded-full text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors" title="Stop Speaking">
                      <Square size={20} fill="currentColor" />
                    </button>
                    <button
                      onClick={sendMessage}
                      disabled={!input.trim()}
                      className={`p-2 rounded-lg transition-all ${input.trim() ? 'bg-black dark:bg-white text-white dark:text-black' : 'bg-gray-200 dark:bg-[#424242] text-gray-400 dark:text-[#2f2f2f] cursor-not-allowed'}`}
                    >
                      <ArrowUp size={20} />
                    </button>
                  </div>
                </div>
              </div>

              {/* Docked Companion Avatar Beside Text Box */}
              {companionConfig.enabled && (companionConfig.positionMode === 'docked' || !companionConfig.positionMode) && (
                <div className="shrink-0 flex items-center justify-center">
                  <OneeFloatingCompanion
                    definition={activeAvatarDef}
                    animation={companionConfig.customExpression ? undefined : avatarAnimation}
                    expression={companionConfig.customExpression || avatarExpression}
                    isListening={isListening}
                    speechText={companionSpeech}
                    size={companionConfig.size || 78}
                    onToggleVoice={toggleVoice}
                    onStopTTS={stopTTS}
                    onTriggerReaction={(anim) => triggerAvatarState(anim, 4000)}
                    positionMode="docked"
                    showSpeechBubble={companionConfig.showSpeechBubble}
                    enableGlow={companionConfig.enableGlow}
                  />
                </div>
              )}
            </div>

            <div className="text-center mt-2 text-xs text-gray-400 dark:text-white/40">
              ALIAS can access your system. Use with caution.
            </div>
          </div>
        </div>

        <SettingsModal
          isOpen={isSettingsOpen}
          onClose={() => setIsSettingsOpen(false)}
          theme={theme}
          setTheme={setTheme}
          voice={voice}
          setVoice={setVoice}
          memories={memories}
          onDeleteMemory={handleDeleteMemory}
          avatarPreset={avatarPreset}
          onSelectAvatarPreset={handleSelectPreset}
          avatarPresets={AVATAR_PRESETS}
          companionSettings={companionConfig}
          onUpdateCompanionSettings={updateCompanionConfig}
          initialTab={settingsInitialTab}
        />
        <ImageModal
          isOpen={isImageModalOpen}
          onClose={() => setIsImageModalOpen(false)}
          onGenerate={handleImageGenerate}
          onGeneratingStart={() => triggerAvatarMood('attentive-left', 0, 'working')}
        />

        {/* Floating Animated Avatar Companion (Bottom-Right Corner Mode) */}
        {companionConfig.enabled && companionConfig.positionMode === 'floating' && (
          <OneeFloatingCompanion
            definition={activeAvatarDef}
            animation={companionConfig.customExpression ? undefined : avatarAnimation}
            expression={companionConfig.customExpression || avatarExpression}
            isListening={isListening}
            speechText={companionSpeech}
            size={companionConfig.size || 78}
            onToggleVoice={toggleVoice}
            onStopTTS={stopTTS}
            onTriggerReaction={(anim) => triggerAvatarState(anim, 4000)}
            positionMode="floating"
            showSpeechBubble={companionConfig.showSpeechBubble}
            enableGlow={companionConfig.enableGlow}
          />
        )}
      </div>
    </div>
  )
}

export default App
