import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  CalendarRange, 
  Receipt, 
  Files, 
  Users, 
  LogOut,
  Bell,
  Target,
  ShieldAlert,
  Mic,
  Sparkles
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useApi } from '../hooks/useApi';
import { format, parseISO } from 'date-fns';

const Layout = () => {
  const { user, logout } = useAuth();
  const { request } = useApi();
  const navigate = useNavigate();
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isListening, setIsListening] = useState(false);
  const [speechFeedback, setSpeechFeedback] = useState('');

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const fetchNotifications = async () => {
    try {
      const list = await request('/notifications');
      setNotifications(list || []);
      const countData = await request('/notifications/count');
      setUnreadCount(countData.unread_count || 0);
    } catch (err) {
      console.error("Notifications fetch failed:", err);
    }
  };

  useEffect(() => {
    if (user) {
      fetchNotifications();
      const interval = setInterval(fetchNotifications, 10000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const handleNotificationClick = async (notif: any) => {
    try {
      await request(`/notifications/${notif.id}/read`, { method: 'PATCH' });
      fetchNotifications();
      setShowNotifications(false);
      if (notif.link) {
        navigate(notif.link);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await request('/notifications/read-all', { method: 'PATCH' });
      fetchNotifications();
    } catch (err) {
      console.error(err);
    }
  };

  const startVoiceCommand = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice command is not supported in this browser. Try Chrome or Edge!");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setSpeechFeedback('Listening for command...');
    };

    recognition.onresult = (event: any) => {
      const speechToText = event.results[0][0].transcript.toLowerCase();
      setSpeechFeedback(`Command: "${speechToText}"`);
      
      setTimeout(() => {
        if (speechToText.includes('leave') || speechToText.includes('time off')) {
          navigate('/leave');
        } else if (speechToText.includes('expense') || speechToText.includes('claim')) {
          navigate('/expenses');
        } else if (speechToText.includes('document') || speechToText.includes('vault')) {
          navigate('/documents');
        } else if (speechToText.includes('onboarding') || speechToText.includes('checklist')) {
          navigate('/onboarding');
        } else if (speechToText.includes('team') || speechToText.includes('directory')) {
          navigate('/team');
        } else if (speechToText.includes('audit')) {
          navigate('/audit');
        } else if (speechToText.includes('dashboard') || speechToText.includes('home')) {
          navigate('/');
        } else {
          setSpeechFeedback(`Unknown command: "${speechToText}"`);
        }
      }, 1000);
    };

    recognition.onerror = (event: any) => {
      console.error("Speech Recognition Error:", event.error);
      setIsListening(false);
      setSpeechFeedback('Error recognizing speech.');
    };

    recognition.onend = () => {
      setIsListening(false);
      setTimeout(() => setSpeechFeedback(''), 3000);
    };

    recognition.start();
  };

  if (!user) return null;

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">
            <Sparkles size={20} />
          </div>
          <div className="sidebar-brand-text">PeopleOS</div>
        </div>
        
        <nav className="sidebar-nav">
          <div className="sidebar-section-title">Main</div>
          <NavLink to="/" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <LayoutDashboard />
            <span>Dashboard</span>
          </NavLink>
          
          <div className="sidebar-section-title">Self Service</div>
          <NavLink to="/leave" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <CalendarRange />
            <span>Leaves</span>
          </NavLink>
          <NavLink to="/expenses" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <Receipt />
            <span>Expenses</span>
          </NavLink>
          <NavLink to="/documents" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <Files />
            <span>Documents</span>
          </NavLink>

          {/* New Hire Section */}
          {user.role === 'employee' && (
            <>
              <div className="sidebar-section-title">Onboarding</div>
              <NavLink to="/onboarding" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
                <Target />
                <span>My Checklist</span>
              </NavLink>
            </>
          )}

          {/* Manager / Admin Section */}
          {(user.role === 'manager' || user.role === 'hr_admin') && (
            <>
              <div className="sidebar-section-title">Management</div>
              <NavLink to="/team" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
                <Users />
                <span>{user.role === 'manager' ? 'My Team' : 'Directory'}</span>
              </NavLink>
              
              {user.role === 'hr_admin' && (
                <NavLink to="/audit" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
                  <ShieldAlert />
                  <span>Audit Logs</span>
                </NavLink>
              )}
            </>
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-avatar">
              {user.name.charAt(0)}
            </div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">{user.name}</div>
              <div className="sidebar-user-role">{user.role.replace('_', ' ')}</div>
            </div>
          </div>
          <button onClick={handleLogout} className="sidebar-link w-full mt-sm" style={{ color: 'var(--error)' }}>
            <LogOut />
            <span>Log out</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="header">
          <div className="header-left">
            {/* Contextual header title could go here if needed, but we rely on page headers */}
          </div>
          <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)', position: 'relative' }}>
            {speechFeedback && (
              <div className="glass-panel shadow-glow" style={{ padding: '8px 16px', borderRadius: '20px', fontSize: '0.85rem', color: 'var(--accent-cyan)', border: '1px solid rgba(0, 240, 255, 0.2)', backgroundColor: 'rgba(0, 240, 255, 0.1)', marginRight: '8px' }}>
                {speechFeedback}
              </div>
            )}
            
            <button 
              style={{ 
                width: '40px', 
                height: '40px', 
                borderRadius: '50%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                backgroundColor: isListening ? 'rgba(255, 0, 127, 0.15)' : 'rgba(255,255,255,0.1)', 
                border: isListening ? '1px solid rgba(255, 0, 127, 0.3)' : '1px solid rgba(255,255,255,0.1)',
                color: isListening ? 'var(--accent-pink)' : 'white',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onClick={startVoiceCommand}
              title="Voice Commands"
            >
              <Mic size={20} className={isListening ? "animate-pulse" : ""} />
            </button>

            <button style={{ 
              width: '40px', 
              height: '40px', 
              borderRadius: '50%', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              backgroundColor: 'rgba(255,255,255,0.1)', 
              border: '1px solid rgba(255,255,255,0.1)',
              color: 'white',
              cursor: 'pointer',
              position: 'relative'
            }} onClick={() => setShowNotifications(!showNotifications)}>
              <Bell size={20} />
              {unreadCount > 0 && (
                <div style={{ position: 'absolute', top: '-4px', right: '-4px', backgroundColor: 'var(--accent-pink)', color: 'white', borderRadius: '50%', width: '18px', height: '18px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.65rem', fontWeight: 'bold', boxShadow: '0 0 10px rgba(255, 0, 127, 0.5)' }}>
                  {unreadCount}
                </div>
              )}
            </button>

            {showNotifications && (
              <div className="glass-panel" style={{
                position: 'absolute',
                top: '55px',
                right: '0',
                width: '320px',
                maxHeight: '380px',
                overflowY: 'auto',
                zIndex: 100,
                padding: 'var(--space-md)',
                border: '1px solid rgba(255,255,255,0.1)',
                boxShadow: 'var(--shadow-glass)',
                backgroundColor: 'rgba(10, 12, 20, 0.95)',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <span className="font-bold text-white text-sm">Notifications</span>
                  {unreadCount > 0 && (
                    <button onClick={handleMarkAllRead} style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', fontSize: '0.75rem', cursor: 'pointer', fontWeight: 600 }}>
                      Mark all read
                    </button>
                  )}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {notifications.length === 0 ? (
                    <div style={{ padding: 'var(--space-md) 0', textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: '0.875rem' }}>
                      No notifications
                    </div>
                  ) : (
                    notifications.map(n => (
                      <div 
                        key={n.id} 
                        onClick={() => handleNotificationClick(n)}
                        style={{ 
                          padding: '10px 12px', 
                          borderRadius: '8px', 
                          backgroundColor: n.read ? 'rgba(255,255,255,0.02)' : 'rgba(255,255,255,0.07)', 
                          border: '1px solid rgba(255,255,255,0.05)',
                          cursor: 'pointer',
                          fontSize: '0.85rem',
                          textAlign: 'left'
                        }}
                      >
                        <div style={{ fontWeight: n.read ? 500 : 700, color: '#fff', marginBottom: '2px' }}>{n.title}</div>
                        <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.75rem' }}>{n.body}</div>
                        <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: '0.7rem', marginTop: '4px' }}>
                          {format(parseISO(n.created_at), 'MMM d, h:mm a')}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </header>
        
        <div className="page">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
