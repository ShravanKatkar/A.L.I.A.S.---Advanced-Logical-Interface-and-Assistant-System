import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Mail, Lock, User, ArrowRight, Loader, Eye, EyeOff, 
  Flame, Settings, X, CheckCircle2, ShieldCheck, ExternalLink, HelpCircle 
} from 'lucide-react';
import { 
  signInWithGoogleFirebase, 
  signInWithEmailFirebase, 
  signUpWithEmailFirebase, 
  isFirebaseConfigured, 
  getFirebaseConfig, 
  saveFirebaseConfig, 
  formatFirebaseError 
} from '../firebase';
import { Avatar } from '@bible-strong/avatar-react';
import avatarDef from '../assets/alien-avatar-definition.json';

export default function Auth({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Interactive Mascot Emotion State (Saksham Gupta style)
  const [avatarAnim, setAvatarAnim] = useState('waking');
  const [avatarExpr, setAvatarExpr] = useState(null);
  const [mascotBubble, setMascotBubble] = useState('Waking up...');
  const mascotTimerRef = useRef(null);

  // Set mascot state with speech bubble and optional reset
  const triggerMascotReaction = (anim, expr = null, bubbleText = '', autoResetMs = 0) => {
    if (mascotTimerRef.current) clearTimeout(mascotTimerRef.current);
    setAvatarAnim(anim);
    setAvatarExpr(expr);
    setMascotBubble(bubbleText);

    if (autoResetMs > 0) {
      mascotTimerRef.current = setTimeout(() => {
        setAvatarAnim('idle');
        setAvatarExpr(null);
        setMascotBubble('');
      }, autoResetMs);
    }
  };

  // Wake up smoothly on page load
  useEffect(() => {
    const timer = setTimeout(() => {
      triggerMascotReaction('idle', null, 'Hello there! Ready when you are.', 3200);
    }, 2200);
    return () => clearTimeout(timer);
  }, []);

  // React to error events
  useEffect(() => {
    if (error) {
      triggerMascotReaction('confused', 'skeptical-left', error.length > 40 ? 'Oops, please check your info!' : error, 4500);
    }
  }, [error]);

  // React to success events
  useEffect(() => {
    if (successMsg) {
      triggerMascotReaction('celebrate', null, 'Woohoo! Welcome aboard! 🎉');
    }
  }, [successMsg]);

  // Playful reactions when user clicks on mascot
  const handleMascotPoke = () => {
    const pokes = [
      { anim: 'playful', expr: null, text: 'Hehe! I\'m Onee, your assistant!' },
      { anim: 'laughing', expr: null, text: 'Ready whenever you are!' },
      { anim: 'curious', expr: 'curious-left', text: 'What shall we build today?' },
      { anim: 'proud', expr: null, text: 'Your intelligent system is online!' },
      { anim: 'excited', expr: 'joyful-wide', text: 'Let\'s create something great!' },
    ];
    const pick = pokes[Math.floor(Math.random() * pokes.length)];
    triggerMascotReaction(pick.anim, pick.expr, pick.text, 3600);
  };

  // Firebase Config State
  const [hasFirebaseConfig, setHasFirebaseConfig] = useState(false);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [configSnippet, setConfigSnippet] = useState('');
  const [configParseError, setConfigParseError] = useState('');

  // 1. Check Firebase configuration on mount
  useEffect(() => {
    const checkConfig = async () => {
      // 1. Check local / env config
      if (isFirebaseConfigured()) {
        setHasFirebaseConfig(true);
        return;
      }

      // 2. Check if backend .env has Firebase credentials
      try {
        const res = await fetch('http://127.0.0.1:8000/api/auth/config');
        if (res.ok) {
          const data = await res.json();
          if (data.firebase && data.firebase.apiKey && data.firebase.projectId) {
            saveFirebaseConfig(data.firebase);
            setHasFirebaseConfig(true);
            return;
          }
        }
      } catch (e) {
        console.warn('Could not fetch backend auth config:', e);
      }

      setHasFirebaseConfig(isFirebaseConfigured());
    };

    checkConfig();
  }, []);

  // 2. Load saved email & password from localStorage
  useEffect(() => {
    const savedEmail = localStorage.getItem('alias_saved_email');
    const savedPassword = localStorage.getItem('alias_saved_password');
    if (savedEmail || savedPassword) {
      setFormData(prev => ({
        ...prev,
        email: savedEmail || '',
        password: savedPassword || ''
      }));
    }
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  // Sync Firebase authenticated user with local backend database
  const syncWithBackend = async (firebaseUser, providerType) => {
    try {
      const response = await fetch('http://127.0.0.1:8000/auth/firebase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: firebaseUser.email,
          name: firebaseUser.name || (formData.name?.trim()) || '',
          picture: firebaseUser.picture || '',
          uid: firebaseUser.uid || '',
          id_token: firebaseUser.idToken || '',
          provider: providerType
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          return data;
        }
      }
    } catch (e) {
      console.warn('Backend /auth/firebase endpoint not yet reachable, continuing with Firebase profile:', e);
    }

    // Graceful fallback: Do not block authenticated user if backend hasn't reloaded yet
    return {
      id: firebaseUser.uid || Date.now(),
      name: firebaseUser.name || firebaseUser.email?.split('@')[0] || 'User',
      email: firebaseUser.email,
      picture: firebaseUser.picture || '',
      provider: providerType || 'firebase'
    };
  };

  // 3. Handle Firebase Google Sign-In
  const handleGoogleSignIn = async () => {
    setError('');
    setSuccessMsg('');
    triggerMascotReaction('working', null, 'Connecting with Google... ⏳');

    if (!hasFirebaseConfig) {
      setIsConfigModalOpen(true);
      triggerMascotReaction('confused', 'skeptical-left', 'Firebase setup needed!', 3500);
      return;
    }

    setGoogleLoading(true);
    try {
      const fbResult = await signInWithGoogleFirebase();
      setSuccessMsg(`Authenticated as ${fbResult.email}`);
      triggerMascotReaction('celebrate', null, 'Welcome aboard with Google! 🎉');

      // Sync with ALIAS backend SQLite
      const backendUser = await syncWithBackend(fbResult, 'google');

      localStorage.setItem('alias_saved_email', fbResult.email);
      onLoginSuccess({
        id: backendUser.id,
        name: backendUser.name,
        email: backendUser.email,
        picture: backendUser.picture,
        provider: 'google'
      });
    } catch (err) {
      console.error('Google Sign-In Error:', err);
      const msg = formatFirebaseError(err);
      setError(msg);
      triggerMascotReaction('confused', 'skeptical-left', 'Sign-in was cancelled or failed.', 4000);
    } finally {
      setGoogleLoading(false);
    }
  };

  // 4. Handle Firebase Email / Password Sign-In & Sign-Up
  const handleEmailAuth = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setLoading(true);
    triggerMascotReaction('working', null, isLogin ? 'Signing you in... ⏳' : 'Setting up your profile... ⏳');

    try {
      if (hasFirebaseConfig) {
        // --- Authenticate via Firebase ---
        let fbResult;
        if (isLogin) {
          fbResult = await signInWithEmailFirebase(formData.email, formData.password);
        } else {
          fbResult = await signUpWithEmailFirebase(formData.name, formData.email, formData.password);
        }

        setSuccessMsg(`Welcome, ${fbResult.name}!`);
        triggerMascotReaction('celebrate', null, 'Success! Unlocking your assistant... 🚀');

        // Sync with ALIAS backend
        const backendUser = await syncWithBackend(fbResult, 'email');

        localStorage.setItem('alias_saved_email', formData.email);
        localStorage.setItem('alias_saved_password', formData.password);

        onLoginSuccess({
          id: backendUser.id,
          name: backendUser.name,
          email: backendUser.email,
          picture: backendUser.picture,
          provider: 'email'
        });
      } else {
        // --- Fallback to Direct Backend Auth if Firebase not yet configured ---
        const endpoint = isLogin ? 'http://127.0.0.1:8000/login' : 'http://127.0.0.1:8000/register';
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: formData.name?.trim() || '',
            email: formData.email.trim(),
            password: formData.password
          }),
        });

        const data = await response.json();
        if (response.ok && data.status === 'success') {
          setSuccessMsg(isLogin ? 'Login successful!' : 'Account registered successfully!');
          setAvatarAnim('celebrate');
          localStorage.setItem('alias_saved_email', formData.email);
          localStorage.setItem('alias_saved_password', formData.password);
          onLoginSuccess(data.user || data);
        } else {
          setError(data.error || 'Authentication failed. Please verify credentials.');
          setAvatarAnim('confused');
          setAvatarExpr('skeptical-left');
        }
      }
    } catch (err) {
      console.error('Email Auth Error:', err);
      setError(formatFirebaseError(err) || 'Authentication service error. Please try again.');
      setAvatarAnim('confused');
      setAvatarExpr('skeptical-left');
    } finally {
      setLoading(false);
    }
  };

  // 5. Parse and Save Firebase Config from user snippet
  const handleSaveConfig = (e) => {
    e.preventDefault();
    setConfigParseError('');

    try {
      let raw = configSnippet.trim();
      if (!raw) {
        setConfigParseError('Please paste your Firebase configuration.');
        return;
      }

      // If user pasted "const firebaseConfig = { ... };" or "firebaseConfig = { ... }"
      if (raw.includes('{') && raw.includes('}')) {
        const startIndex = raw.indexOf('{');
        const endIndex = raw.lastIndexOf('}');
        raw = raw.substring(startIndex, endIndex + 1);
      }

      // Parse JSON-like or JS object
      let parsed;
      try {
        parsed = JSON.parse(raw);
      } catch (jsonErr) {
        // Attempt relaxed JS object evaluation
        try {
          const fn = new Function(`return (${raw})`);
          parsed = fn();
        } catch (evalErr) {
          throw new Error('Could not parse configuration. Ensure it contains apiKey, authDomain, and projectId.');
        }
      }

      if (!parsed || !parsed.apiKey || !parsed.projectId) {
        throw new Error('Config missing required keys: apiKey and projectId.');
      }

      saveFirebaseConfig(parsed);
      setHasFirebaseConfig(true);
      setIsConfigModalOpen(false);
      setError('');
      setSuccessMsg('Firebase configured successfully!');
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (err) {
      setConfigParseError(err.message || 'Invalid Firebase configuration.');
    }
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center bg-[#090a0f] overflow-hidden text-[#ececec] px-4 py-8">
      {/* Ambient Pulsing Glow Backdrop */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none flex items-center justify-center">
        <div className="absolute w-[800px] h-[800px] bg-amber-600/10 rounded-full blur-[140px] mix-blend-screen opacity-50 animate-pulse" />
        <div className="absolute -top-1/4 -right-1/4 w-[700px] h-[700px] bg-orange-600/15 rounded-full blur-[140px] mix-blend-screen opacity-40 delay-1000 animate-pulse" />
        <div className="absolute -bottom-1/4 -left-1/4 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[120px] mix-blend-screen opacity-30" />
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 30, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="relative w-full max-w-md p-8 md:p-10 pt-10 bg-[#12131a]/85 backdrop-blur-2xl border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.6)] rounded-3xl z-10 mt-14"
      >
        {/* Interactive Mascot Avatar (Instagram Reel / Saksham Gupta style) */}
        <div className="relative flex flex-col items-center -mt-24 mb-4">
          {/* Reaction Speech Bubble */}
          <AnimatePresence>
            {mascotBubble && (
              <motion.div
                key="mascot-bubble"
                initial={{ opacity: 0, y: 10, scale: 0.88 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.88 }}
                transition={{ duration: 0.2 }}
                className="absolute -top-11 z-30 px-3.5 py-1.5 rounded-full bg-white text-gray-900 text-xs font-semibold shadow-2xl border border-white/30 whitespace-nowrap flex items-center gap-1.5 pointer-events-none"
              >
                <span>{mascotBubble}</span>
                <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2.5 h-2.5 bg-white rotate-45" />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Interactive Mascot Avatar */}
          <div 
            onClick={handleMascotPoke}
            title="Click to interact with ALIAS Alien Companion!"
            className="relative cursor-pointer group"
          >
            <div className="absolute inset-0 rounded-full bg-lime-500/25 blur-xl group-hover:bg-lime-400/35 transition-all duration-300 -z-10" />
            <div className="w-28 h-28 md:w-32 md:h-32 rounded-full bg-[#151622]/95 border-2 border-lime-500/30 p-1 shadow-[0_12px_45px_rgba(0,0,0,0.6)] flex items-center justify-center transition-transform duration-200 group-hover:scale-105 overflow-hidden">
              <Avatar
                definition={avatarDef}
                animation={avatarExpr ? undefined : avatarAnim}
                expression={avatarExpr || undefined}
                size={110}
                className="select-none pointer-events-none"
              />
            </div>
            {/* Live Indicator Pulse */}
            <span className="absolute bottom-1 right-2 w-3.5 h-3.5 rounded-full bg-emerald-400 border-2 border-[#12131a] shadow-sm animate-pulse" />
          </div>
        </div>

        {/* Top Header */}
        <div className="flex flex-col items-center mb-6">
          <h2 className="text-2xl md:text-3xl font-light text-center tracking-tight text-white flex items-center gap-2">
            ALIAS <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 font-medium">2.0</span>
          </h2>
          
          <div className="flex items-center gap-2 mt-2">
            {hasFirebaseConfig ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                <Flame size={12} className="text-amber-400" /> Firebase Auth Active
              </span>
            ) : (
              <button
                type="button"
                onClick={() => setIsConfigModalOpen(true)}
                className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-amber-500/15 text-amber-300 border border-amber-500/30 hover:bg-amber-500/25 transition-colors cursor-pointer"
              >
                <Flame size={12} className="text-amber-400 animate-pulse" /> Connect Firebase
              </button>
            )}
          </div>

          <p className="text-white/40 text-center mt-2 text-xs md:text-sm">
            {isLogin ? 'Sign in to access your intelligent workspace' : 'Create an account to start collaborating'}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex p-1 bg-black/40 border border-white/10 rounded-2xl mb-6">
          <button
            type="button"
            onClick={() => { setIsLogin(true); setError(''); }}
            className={`flex-1 py-2 text-sm font-medium rounded-xl transition-all duration-200 ${
              isLogin ? 'bg-white/15 text-white shadow-sm' : 'text-white/40 hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsLogin(false); setError(''); }}
            className={`flex-1 py-2 text-sm font-medium rounded-xl transition-all duration-200 ${
              !isLogin ? 'bg-white/15 text-white shadow-sm' : 'text-white/40 hover:text-white'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Error / Success Notifications */}
        <AnimatePresence mode="wait">
          {error && (
            <motion.div 
              initial={{ opacity: 0, y: -10, height: 0 }} 
              animate={{ opacity: 1, y: 0, height: 'auto' }} 
              exit={{ opacity: 0, y: -10, height: 0 }}
              className="mb-4 p-3 rounded-xl bg-red-500/15 border border-red-500/30 text-red-300 text-xs md:text-sm text-center flex items-center justify-center gap-2"
            >
              <span>{error}</span>
            </motion.div>
          )}

          {successMsg && (
            <motion.div 
              initial={{ opacity: 0, y: -10, height: 0 }} 
              animate={{ opacity: 1, y: 0, height: 'auto' }} 
              exit={{ opacity: 0, y: -10, height: 0 }}
              className="mb-4 p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs md:text-sm text-center flex items-center justify-center gap-2"
            >
              <CheckCircle2 size={16} />
              <span>{successMsg}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* SECTION 1: FIREBASE GOOGLE SIGN-IN */}
        <div className="space-y-3 mb-6">
          <button
            type="button"
            onClick={handleGoogleSignIn}
            disabled={googleLoading}
            className="w-full relative flex items-center justify-center gap-3 py-3 px-4 bg-white/5 hover:bg-white/10 active:bg-white/15 border border-white/15 hover:border-white/25 rounded-2xl font-medium text-white text-sm transition-all shadow-sm group cursor-pointer disabled:opacity-60"
          >
            {googleLoading ? (
              <Loader className="animate-spin text-white/70" size={18} />
            ) : (
              <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z"/>
                <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"/>
                <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
                <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
              </svg>
            )}
            <span>
              {googleLoading ? 'Connecting to Google...' : isLogin ? 'Sign in with Google' : 'Sign up with Google'}
            </span>
            <span className="ml-auto flex items-center gap-1 text-[10px] text-amber-400/80 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
              <Flame size={10} /> Firebase
            </span>
          </button>

          {/* Setup / Settings Shortcut */}
          <div className="flex justify-between items-center px-1 text-[11px] text-white/35">
            <span>Powered by Firebase Auth</span>
            <button
              type="button"
              onClick={() => setIsConfigModalOpen(true)}
              className="hover:text-amber-300 transition-colors flex items-center gap-1 cursor-pointer"
            >
              <Settings size={12} />
              <span>{hasFirebaseConfig ? 'Firebase Settings' : 'Configure Firebase'}</span>
            </button>
          </div>
        </div>

        {/* OR DIVIDER */}
        <div className="relative flex items-center justify-center my-6">
          <div className="border-t border-white/10 w-full"></div>
          <span className="bg-[#12131a] px-3 text-[11px] font-semibold text-white/35 uppercase tracking-wider relative z-10">
            Or with email
          </span>
        </div>

        {/* SECTION 2: EMAIL & PASSWORD FORM (FIREBASE OR LOCAL) */}
        <form onSubmit={handleEmailAuth} className="space-y-3.5">
          <AnimatePresence mode="popLayout">
            {!isLogin && (
              <motion.div
                key="name-field"
                initial={{ opacity: 0, height: 0, y: -10 }}
                animate={{ opacity: 1, height: 'auto', y: 0 }}
                exit={{ opacity: 0, height: 0, y: -10 }}
                transition={{ duration: 0.25 }}
              >
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-white/30 group-focus-within:text-amber-400 transition-colors">
                    <User size={17} />
                  </div>
                  <input
                    type="text"
                    name="name"
                    placeholder="Full Name"
                    value={formData.name}
                    onChange={handleChange}
                    onFocus={() => {
                      triggerMascotReaction('listening', 'attentive-left', 'Nice to meet you! What should I call you?');
                    }}
                    onBlur={() => {
                      triggerMascotReaction('idle', null, '');
                    }}
                    required={!isLogin}
                    autoComplete="name"
                    className="w-full pl-10 pr-4 py-3 bg-black/40 border border-white/10 rounded-2xl outline-none text-white placeholder:text-white/30 focus:border-amber-500/50 focus:bg-white/5 transition-all text-sm"
                  />
                </div>
              </motion.div>
            )}

            <motion.div layout key="email-field">
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-white/30 group-focus-within:text-amber-400 transition-colors">
                  <Mail size={17} />
                </div>
                <input
                  type="email"
                  name="email"
                  placeholder="Email Address"
                  value={formData.email}
                  onChange={handleChange}
                  onFocus={() => {
                    triggerMascotReaction('listening', 'attentive-left', 'Watching attentively... 👀');
                  }}
                  onBlur={() => {
                    if (formData.email && !formData.email.includes('@')) {
                      triggerMascotReaction('confused', 'skeptical-left', 'Hmm, is that a valid email? 🤔', 3500);
                    } else if (formData.email) {
                      triggerMascotReaction('happy', null, 'Looking great! ✨', 2200);
                    } else {
                      triggerMascotReaction('idle', null, '');
                    }
                  }}
                  required
                  autoComplete="email"
                  className="w-full pl-10 pr-4 py-3 bg-black/40 border border-white/10 rounded-2xl outline-none text-white placeholder:text-white/30 focus:border-amber-500/50 focus:bg-white/5 transition-all text-sm"
                />
              </div>
            </motion.div>

            <motion.div layout key="password-field">
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-white/30 group-focus-within:text-amber-400 transition-colors">
                  <Lock size={17} />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  placeholder="Password (min 6 characters)"
                  value={formData.password}
                  onChange={handleChange}
                  onFocus={() => {
                    if (showPassword) {
                      triggerMascotReaction('surprised', 'surprised-left', 'Whoa, look away! 🙈');
                    } else {
                      triggerMascotReaction('shy', 'eyes-closed', 'I won\'t peek! 🙈 Eyes closed!');
                    }
                  }}
                  onBlur={() => {
                    if (formData.password && formData.password.length < 6) {
                      triggerMascotReaction('confused', 'uneasy-left', 'Password needs at least 6 characters! 🔒', 3500);
                    } else {
                      triggerMascotReaction('idle', null, '');
                    }
                  }}
                  required
                  autoComplete={isLogin ? "current-password" : "new-password"}
                  className="w-full pl-10 pr-11 py-3 bg-black/40 border border-white/10 rounded-2xl outline-none text-white placeholder:text-white/30 focus:border-amber-500/50 focus:bg-white/5 transition-all text-sm"
                />
                <button
                  type="button"
                  onClick={() => {
                    const next = !showPassword;
                    setShowPassword(next);
                    if (next) {
                      triggerMascotReaction('surprised', 'eyes-closed', '🙈 Don\'t worry, I\'m not looking!');
                    } else {
                      triggerMascotReaction('idle', null, '');
                    }
                  }}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-white/30 hover:text-white/70 transition-colors cursor-pointer"
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </motion.div>
          </AnimatePresence>

          <motion.button
            layout
            type="submit"
            disabled={loading || googleLoading}
            className="w-full relative flex items-center justify-center py-3.5 px-4 bg-gradient-to-r from-white to-gray-200 hover:from-gray-100 hover:to-gray-300 text-black rounded-2xl font-medium mt-4 shadow-md transition-all disabled:opacity-60 disabled:cursor-not-allowed group cursor-pointer"
          >
            {loading ? (
              <Loader className="animate-spin text-black/60" size={19} />
            ) : (
              <span className="flex items-center gap-2 text-sm font-semibold">
                {isLogin ? 'Sign In with Email' : 'Create Account'}
                <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </span>
            )}
          </motion.button>
        </form>

        {/* Bottom Switcher */}
        <motion.div layout className="mt-6 text-center">
          <button
            type="button"
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
              setFormData(prev => ({ ...prev, name: '' }));
            }}
            className="text-xs text-white/40 hover:text-white transition-colors cursor-pointer"
          >
            {isLogin ? (
              <span>Don't have an account yet? <strong className="text-white/80 font-medium">Sign up</strong></span>
            ) : (
              <span>Already have an account? <strong className="text-white/80 font-medium">Sign in</strong></span>
            )}
          </button>
        </motion.div>
      </motion.div>

      {/* MODAL: Firebase Setup & Configuration Dialog */}
      <AnimatePresence>
        {isConfigModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-lg bg-[#151620] border border-white/15 rounded-3xl p-6 md:p-8 shadow-2xl relative text-[#ececec]"
            >
              <button
                onClick={() => setIsConfigModalOpen(false)}
                className="absolute top-4 right-4 text-white/40 hover:text-white transition-colors p-1.5 rounded-xl hover:bg-white/5 cursor-pointer"
              >
                <X size={18} />
              </button>

              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-2xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center">
                  <Flame size={22} />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-white">Firebase Authentication Setup</h3>
                  <p className="text-xs text-white/40">Connect your Firebase Project to ALIAS</p>
                </div>
              </div>

              <div className="text-xs text-white/70 space-y-2 mb-4 bg-white/5 p-3.5 rounded-2xl border border-white/10">
                <p className="font-semibold text-white/90 flex items-center gap-1.5">
                  <HelpCircle size={14} className="text-amber-400" /> How to get your Firebase configuration:
                </p>
                <ol className="list-decimal list-inside space-y-1 text-white/60">
                  <li>Open <a href="https://console.firebase.google.com" target="_blank" rel="noreferrer" className="text-amber-400 hover:underline">Firebase Console</a></li>
                  <li>Navigate to <strong>Project Settings &gt; General &gt; Your apps &gt; Web App</strong></li>
                  <li>Under <strong>Firebase SDK snippet &gt; Config</strong>, copy the <code className="bg-white/10 px-1 py-0.5 rounded text-amber-300">firebaseConfig</code> block</li>
                  <li>Make sure <strong>Google</strong> & <strong>Email/Password</strong> are enabled in <strong>Authentication &gt; Sign-in method</strong></li>
                </ol>
              </div>

              {configParseError && (
                <div className="mb-4 p-2.5 rounded-xl bg-red-500/15 border border-red-500/30 text-red-300 text-xs">
                  {configParseError}
                </div>
              )}

              <form onSubmit={handleSaveConfig} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-white/80 mb-1.5">
                    Paste Firebase Config (JSON or JavaScript snippet):
                  </label>
                  <textarea
                    rows={7}
                    placeholder={`const firebaseConfig = {\n  apiKey: "AIzaSy...",\n  authDomain: "your-app.firebaseapp.com",\n  projectId: "your-app",\n  storageBucket: "your-app.appspot.com",\n  messagingSenderId: "123456789",\n  appId: "1:123456:web:abcd"\n};`}
                    value={configSnippet}
                    onChange={(e) => setConfigSnippet(e.target.value)}
                    required
                    className="w-full px-3.5 py-2.5 bg-black/60 border border-white/15 rounded-xl text-xs text-amber-200 outline-none focus:border-amber-400 focus:bg-white/5 transition-all font-mono placeholder:text-white/20"
                  />
                </div>

                <div className="flex gap-2 justify-end pt-2">
                  <button
                    type="button"
                    onClick={() => setIsConfigModalOpen(false)}
                    className="px-4 py-2.5 rounded-xl text-xs text-white/60 hover:text-white hover:bg-white/5 transition-all cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-black font-semibold rounded-xl text-xs transition-all shadow-lg shadow-amber-500/20 cursor-pointer"
                  >
                    Save & Activate Firebase
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
