import { useState, useEffect, useRef } from 'react'
import io from 'socket.io-client'
import {
  Plus, MessageSquare, ChevronDown, Square,
  Paperclip, Mic, ArrowUp, Menu, X, Settings, Terminal, Thermometer, Cpu, Check, Copy, User, Image, Search, Trash2, Edit2
} from 'lucide-react'
import Auth from './components/Auth'
import SettingsModal from './components/SettingsModal'
import ImageModal from './components/ImageModal'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'

// Connect to the Python Backend
// Connect to the Python Backend
const socket = io('http://127.0.0.1:8000', {
  transports: ['websocket', 'polling']
})

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
  const [theme, setTheme] = useState('system') // 'light', 'dark', 'system'
  const [voice, setVoice] = useState('male') // 'male', 'female'
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)

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
      }
    })

    socket.on('chat_start', (data) => {
      setMessages(prev => [...prev, { role: 'ai', text: '', isStreaming: true }])
    })

    socket.on('chat_chunk', (data) => {
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
      setMessages(prev => {
        const updated = [...prev]
        if (updated.length > 0 && updated[updated.length - 1].role === 'ai') {
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            isStreaming: false
          }
        }
        return updated
      })
    })

    socket.on('status', (data) => {
      setIsListening(data.status === 'listening')
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
        console.log("Upload success:", data)
      } else {
        addMessage('system', `Upload failed: ${data.error}`)
      }
    } catch (error) {
      console.error('Upload Error:', error)
      addMessage('system', 'Upload failed (Network Error)')
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
    addMessage('user', input)
    socket.emit('process_text', {
      text: input,
      temperature: parseFloat(temperature),
      model: selectedModel,
      username: user ? user.name : 'Guest',
      email: user ? user.email : 'guest@alias.com',
      conversation_id: currentConversationId
    })
    setInput('')
  }

  const handleImageGenerate = ({ prompt, width, height, model }) => {
    const commandText = `generate image of ${prompt} ${width}x${height} using ${model}`
    addMessage('user', `Generate image: "${prompt}" (${width}x${height}, model: ${model})`)
    socket.emit('process_text', {
      text: commandText,
      temperature: parseFloat(temperature),
      model: selectedModel,
      username: user ? user.name : 'Guest',
      email: user ? user.email : 'guest@alias.com',
      conversation_id: currentConversationId
    })
  }

  const startNewChat = () => {
    setMessages([])
    setInput('')
    setCurrentConversationId(null)
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
          <button onClick={() => setIsSettingsOpen(true)} className="w-full flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-gray-200 dark:hover:bg-[#212121] transition-colors">
            <Settings size={18} className="text-gray-500 dark:text-white/70" />
            <div className="flex-1 text-left text-sm font-medium text-gray-700 dark:text-white">
              Settings
            </div>
          </button>
          <button onClick={() => { setIsAuthenticated(false); setUser(null); localStorage.removeItem('alias_user'); }} className="w-full flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-gray-200 dark:hover:bg-[#212121] transition-colors">
            <User size={18} className="text-gray-500 dark:text-white/70" />
            <div className="flex-1 text-left text-sm font-medium text-red-500">
              Sign Out
            </div>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col bg-white dark:bg-[#212121] relative min-w-0 transition-colors duration-200">

        {/* Top Bar (Mobile/Collapsed) */}
        <header className="flex items-center p-4 sticky top-0 z-10">
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
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center px-4">
              <div className="w-24 h-24 mb-6 rounded-full overflow-hidden shadow-lg dark:shadow-[0_0_30px_rgba(255,255,255,0.1)]">
                <img src="/logo.png" alt="ALIAS" className="w-full h-full object-cover" />
              </div>

              <h2 className="text-2xl font-semibold mb-8 text-gray-900 dark:text-white">How can I assist you?</h2>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto pt-10 px-4 pb-32 space-y-6">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'ai' && (
                    <div className="w-8 h-8 rounded-full bg-black dark:bg-white flex items-center justify-center shrink-0 mt-1 overflow-hidden">
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
                            code: CodeBlock
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
            <div className="bg-gray-50 dark:bg-[#2f2f2f] rounded-[26px] p-2 flex flex-col relative focus-within:ring-1 focus-within:ring-black/10 dark:focus-within:ring-white/20 transition-shadow">

              {/* Input Top Actions */}
              <div className="flex items-end gap-2 px-2">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
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
        />
        <ImageModal
          isOpen={isImageModalOpen}
          onClose={() => setIsImageModalOpen(false)}
          onGenerate={handleImageGenerate}
        />
      </div>
    </div>
  )
}

export default App
