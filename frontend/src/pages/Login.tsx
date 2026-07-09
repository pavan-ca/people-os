import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogIn, UserPlus, ShieldCheck, Zap, Sparkles } from 'lucide-react';

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  
  // Login State
  const [email, setEmail] = useState('priya.sharma@peopleos.io');
  const [password, setPassword] = useState('Admin@123');
  
  // Signup State
  const [name, setName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        const errorMsg = Array.isArray(data.detail) ? data.detail[0].msg : (data.detail || 'Login failed');
        throw new Error(errorMsg);
      }

      const userRes = await fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${data.access_token}` }
      });
      const userData = await userRes.json();

      login(data.access_token, userData);
      navigate('/');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);
    
    // Simulate signup for the demo (since HR creates users in reality)
    setTimeout(() => {
      setLoading(false);
      setSuccess('Application submitted! HR will review your registration shortly.');
      setName('');
      setSignupEmail('');
      setSignupPassword('');
    }, 1500);
  };

  return (
    <div className="split-layout">
      {/* LEFT COLUMN: The Form */}
      <div className="split-left">
        <div className="w-full" style={{ maxWidth: '440px' }}>
          
          <div className="flex items-center gap-md mb-2xl">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-accent-cyan to-accent-purple flex items-center justify-center text-white shadow-glow">
              <Sparkles size={24} />
            </div>
            <span className="font-bold text-3xl font-display tracking-tight text-white">PeopleOS</span>
          </div>

          <div className="mb-xl">
            <h1 className="text-4xl font-bold mb-xs text-white">
              {isLogin ? 'Welcome back' : 'Join PeopleOS'}
            </h1>
            <p className="text-muted text-lg">
              {isLogin ? 'Log in to your workspace.' : 'Request access to the platform.'}
            </p>
          </div>

          {error && <div className="p-md rounded-lg bg-error/10 border border-error/20 text-error mb-md font-medium text-sm">{error}</div>}
          {success && <div className="p-md rounded-lg bg-success/10 border border-success/20 text-success mb-md font-medium text-sm">{success}</div>}

          {isLogin ? (
            <form onSubmit={handleLogin} className="flex-col gap-md animate-in">
              <div className="input-group">
                <label className="input-label">Work Email</label>
                <input 
                  type="email" 
                  className="input" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="input-group">
                <label className="input-label">Password</label>
                <input 
                  type="password" 
                  className="input" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn btn-primary btn-lg mt-sm shadow-glow" style={{ width: '100%' }} disabled={loading}>
                {loading ? <span className="spinner"></span> : <><LogIn size={20} /> Sign In</>}
              </button>

              <div style={{ position: 'relative', margin: 'var(--space-md) 0', textAlign: 'center' }}>
                <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, borderTop: '1px solid rgba(255,255,255,0.1)' }}></div>
                <span style={{ position: 'relative', backgroundColor: 'var(--bg-base)', padding: '0 var(--space-md)', color: 'rgba(255,255,255,0.5)', fontSize: '0.875rem' }}>or</span>
              </div>
              
              <button 
                type="button" 
                onClick={() => setIsLogin(false)} 
                className="btn btn-lg" 
                style={{ width: '100%', backgroundColor: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid rgba(255,255,255,0.1)' }}
              >
                <UserPlus size={20} /> Create an account
              </button>
            </form>
          ) : (
            <form onSubmit={handleSignup} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }} className="animate-in">
              <div className="input-group">
                <label className="input-label">Full Name</label>
                <input 
                  type="text" 
                  className="input" 
                  placeholder="e.g. Alex Morgan"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
              <div className="input-group">
                <label className="input-label">Work Email</label>
                <input 
                  type="email" 
                  className="input" 
                  placeholder="name@company.com"
                  value={signupEmail}
                  onChange={(e) => setSignupEmail(e.target.value)}
                  required
                />
              </div>
              <div className="input-group">
                <label className="input-label">Password</label>
                <input 
                  type="password" 
                  className="input" 
                  placeholder="Create a strong password"
                  value={signupPassword}
                  onChange={(e) => setSignupPassword(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="btn btn-primary btn-lg mt-sm shadow-glow" style={{ width: '100%' }} disabled={loading}>
                {loading ? <span className="spinner"></span> : <><UserPlus size={20} /> Request Access</>}
              </button>

              <div style={{ position: 'relative', margin: 'var(--space-md) 0', textAlign: 'center' }}>
                <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, borderTop: '1px solid rgba(255,255,255,0.1)' }}></div>
                <span style={{ position: 'relative', backgroundColor: 'var(--bg-base)', padding: '0 var(--space-md)', color: 'rgba(255,255,255,0.5)', fontSize: '0.875rem' }}>or</span>
              </div>
              
              <button 
                type="button" 
                onClick={() => setIsLogin(true)} 
                className="btn btn-lg" 
                style={{ width: '100%', backgroundColor: 'rgba(255,255,255,0.05)', color: 'white', border: '1px solid rgba(255,255,255,0.1)' }}
              >
                <LogIn size={20} /> Back to Sign In
              </button>
            </form>
          )}
        </div>
      </div>

      {/* RIGHT COLUMN: The Showcase */}
      <div className="split-right">
        {/* We reuse the animated mesh gradient from index.css implicitly by letting it show through the transparent background */}
        
        {/* Showcase Container (Clean Typography, Boxless) */}
        <div className="relative z-10 text-left" style={{ width: '100%', maxWidth: '580px', padding: '0 var(--space-xl)' }}>
          <div className="mb-lg" style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 'var(--space-md)' }}>
            <div 
              style={{ 
                width: '56px', 
                height: '56px', 
                borderRadius: '16px', 
                background: 'linear-gradient(135deg, var(--accent-purple), var(--accent-cyan))', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                color: 'white', 
                boxShadow: 'var(--shadow-glow)' 
              }}
            >
              <Sparkles size={28} />
            </div>
          </div>
          
          <h2 className="text-4xl font-bold text-white mb-md leading-tight tracking-tight" style={{ fontSize: '2.75rem', lineHeight: '1.2' }}>
            The HR platform that actually <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent-cyan to-accent-purple">works for you.</span>
          </h2>
          
          <p className="text-lg text-white/70 mb-2xl leading-relaxed" style={{ fontSize: '1.125rem' }}>
            Experience the first fully contextual, event-driven employee portal. No more forms. No more chasing approvals. Just frictionless execution.
          </p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)', marginTop: 'var(--space-xl)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', padding: 'var(--space-xs) 0' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: 'rgba(0, 240, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-cyan)', flexShrink: 0 }}>
                <Zap size={20} />
              </div>
              <div>
                <div className="font-bold text-white text-base">Event-Driven Onboarding</div>
                <div className="text-sm text-muted" style={{ marginTop: '2px' }}>Automated workflows that trigger instantly.</div>
              </div>
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)', padding: 'var(--space-xs) 0' }}>
              <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: 'rgba(168, 85, 247, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-purple)', flexShrink: 0 }}>
                <ShieldCheck size={20} />
              </div>
              <div>
                <div className="font-bold text-white text-base">API-Enforced RBAC</div>
                <div className="text-sm text-muted" style={{ marginTop: '2px' }}>Bank-grade security embedded at every layer.</div>
              </div>
            </div>
          </div>
          
          {/* Decorative blurred circles behind the glass */}
          <div className="absolute -top-20 -right-20 w-64 h-64 bg-accent-cyan rounded-full mix-blend-screen filter blur-[100px] opacity-40 animate-pulse"></div>
          <div className="absolute -bottom-20 -left-20 w-80 h-80 bg-accent-purple rounded-full mix-blend-screen filter blur-[120px] opacity-40"></div>
        </div>
      </div>
    </div>
  );
};

export default Login;
