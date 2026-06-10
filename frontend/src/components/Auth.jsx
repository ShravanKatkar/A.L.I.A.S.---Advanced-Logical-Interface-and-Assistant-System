import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, Lock, User, ArrowRight, Loader } from 'lucide-react';

export default function Auth({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Load saved credentials on mount
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? 'http://127.0.0.1:8000/login' : 'http://127.0.0.1:8000/register';
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(isLogin 
          ? { email: formData.email, password: formData.password }
          : formData
        ),
      });

      const data = await response.json();

      if (data.status === 'success') {
        // Save credentials locally for next time
        localStorage.setItem('alias_saved_email', formData.email);
        localStorage.setItem('alias_saved_password', formData.password);
        
        // Pass user details up to App.jsx
        onLoginSuccess({
           id: data.id,
           name: data.name,
           email: data.email
        });
      } else {
        setError(data.error || 'Authentication failed');
      }
    } catch (err) {
      setError('Network error. Please make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center bg-[#0a0a0a] overflow-hidden text-[#ececec]">
      {/* Dynamic Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none flex items-center justify-center">
         <div className="absolute w-[800px] h-[800px] bg-red-600/10 rounded-full blur-[120px] mix-blend-screen opacity-50 animate-pulse" />
         <div className="absolute top-1/4 -right-1/4 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[120px] mix-blend-screen opacity-40 delay-1000 animate-pulse" />
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 30, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="relative w-full max-w-md p-8 md:p-10 mx-4 bg-white/5 backdrop-blur-xl border border-white/10 shadow-2xl rounded-3xl z-10"
      >
        <div className="flex justify-center mb-8">
          <div className="w-16 h-16 rounded-full overflow-hidden shadow-[0_0_30px_rgba(255,255,255,0.1)] border border-white/10 relative">
            <img src="/logo.png" alt="ALIAS" className="w-full h-full object-cover" />
            <div className="absolute inset-0 bg-white/10 mix-blend-overlay"></div>
          </div>
        </div>

        <h2 className="text-3xl font-light text-center mb-2 tracking-tight">
          {isLogin ? 'Welcome back' : 'Create an account'}
        </h2>
        <p className="text-white/40 text-center mb-8 text-sm">
          {isLogin ? 'Log in to continue to ALIAS' : 'Join ALIAS to start interacting'}
        </p>

        {error && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }} 
            animate={{ opacity: 1, height: 'auto' }} 
            className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center"
          >
            {error}
          </motion.div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <AnimatePresence mode="popLayout">
            {!isLogin && (
              <motion.div
                key="name"
                initial={{ opacity: 0, height: 0, y: -20 }}
                animate={{ opacity: 1, height: 'auto', y: 0 }}
                exit={{ opacity: 0, height: 0, y: -20 }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
              >
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-white/30 group-focus-within:text-white/70 transition-colors">
                    <User size={18} />
                  </div>
                  <input
                    type="text"
                    name="name"
                    placeholder="Your Name"
                    value={formData.name}
                    onChange={handleChange}
                    required={!isLogin}
                    autoComplete="name"
                    className="w-full pl-11 pr-4 py-3.5 bg-black/40 border border-white/10 rounded-2xl outline-none text-white placeholder:text-white/30 focus:border-white/30 focus:bg-white/5 transition-all text-sm"
                  />
                </div>
              </motion.div>
            )}
            <motion.div layout key="email">
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-white/30 group-focus-within:text-white/70 transition-colors">
                  <Mail size={18} />
                </div>
                <input
                  type="email"
                  name="email"
                  placeholder="Email Address"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  autoComplete="email"
                  className="w-full pl-11 pr-4 py-3.5 bg-black/40 border border-white/10 rounded-2xl outline-none text-white placeholder:text-white/30 focus:border-white/30 focus:bg-white/5 transition-all text-sm"
                />
              </div>
            </motion.div>

            <motion.div layout key="password">
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-white/30 group-focus-within:text-white/70 transition-colors">
                  <Lock size={18} />
                </div>
                <input
                  type="password"
                  name="password"
                  placeholder="Password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  autoComplete={isLogin ? "current-password" : "new-password"}
                  className="w-full pl-11 pr-4 py-3.5 bg-black/40 border border-white/10 rounded-2xl outline-none text-white placeholder:text-white/30 focus:border-white/30 focus:bg-white/5 transition-all text-sm"
                />
              </div>
            </motion.div>
          </AnimatePresence>

          <motion.button
            layout
            type="submit"
            disabled={loading}
            className="w-full relative flex items-center justify-center py-3.5 px-4 bg-white hover:bg-gray-100 text-black rounded-2xl font-medium mt-6 overflow-hidden transition-all disabled:opacity-70 disabled:cursor-not-allowed group"
          >
            {loading ? (
              <Loader className="animate-spin text-black/50" size={20} />
            ) : (
              <span className="flex items-center gap-2">
                {isLogin ? 'Sign In' : 'Create Account'}
                <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </span>
            )}
          </motion.button>
        </form>

        <motion.div layout className="mt-8 text-center">
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
              // Just clearing the name, but remembering email and password
              setFormData(prev => ({ ...prev, name: '' }));
            }}
            className="text-sm text-white/40 hover:text-white transition-colors"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </motion.div>
      </motion.div>
    </div>
  );
}
