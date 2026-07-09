import React, { useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useAuth } from '../contexts/AuthContext';
import { format, parseISO, addMonths, subMonths } from 'date-fns';
import { CalendarRange, Plus, Check, X, Clock, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';

const Leave = () => {
  const { request, loading } = useApi();
  const { user } = useAuth();
  
  const [activeTab, setActiveTab] = useState<'my_leaves' | 'team_queue'>(
    (user?.role === 'manager' || user?.role === 'hr_admin') ? 'team_queue' : 'my_leaves'
  );
  
  // My Leaves State
  const [balances, setBalances] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  
  // Manager State
  const [queue, setQueue] = useState<any[]>([]);

  // Team Calendar State
  const [currentDate, setCurrentDate] = useState(new Date());
  const [teamLeaves, setTeamLeaves] = useState<any[]>([]);

  const [showApplyModal, setShowApplyModal] = useState(false);
  const [formData, setFormData] = useState({
    leave_type: 'casual',
    start_date: '',
    end_date: '',
    reason: ''
  });

  const fetchData = async () => {
    try {
      const [balRes, histRes] = await Promise.all([
        request('/leave/balances'),
        request('/leave/requests/mine')
      ]);
      setBalances(balRes);
      setHistory(histRes);

      // Try fetching queue (will fail for non-managers, that's fine)
      try {
        const queueRes = await request('/leave/requests/pending/queue');
        setQueue(queueRes || []);
      } catch (e) {
        // Not a manager
      }

      // Fetch team leaves for calendar
      try {
        const month = currentDate.getMonth() + 1;
        const year = currentDate.getFullYear();
        const calRes = await request(`/leave/team/calendar?month=${month}&year=${year}`);
        setTeamLeaves(calRes || []);
      } catch (e) {
        // Fail silently
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchData();
  }, [request, currentDate]);

  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await request('/leave/apply', {
        method: 'POST',
        body: formData
      });
      setShowApplyModal(false);
      setFormData({ leave_type: 'casual', start_date: '', end_date: '', reason: '' });
      fetchData();
    } catch (err) {
      alert("Failed to apply for leave");
    }
  };

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    try {
      await request(`/leave/requests/${id}/action`, {
        method: 'POST',
        body: { action }
      });
      fetchData();
    } catch (err) {
      alert(`Failed to ${action} leave`);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved': return <span className="badge badge-approved">Approved</span>;
      case 'rejected': return <span className="badge badge-rejected">Rejected</span>;
      default: return <span className="badge badge-pending">Pending</span>;
    }
  };

  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  
  const handlePrevMonth = () => {
    setCurrentDate(subMonths(currentDate, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(addMonths(currentDate, 1));
  };

  const renderCalendar = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth() + 1;
    
    const daysInMonth = new Date(year, month, 0).getDate();
    const firstDayIndex = new Date(year, month - 1, 1).getDay(); // Sun = 0
    
    const days = [];
    // Blank days
    for (let i = 0; i < firstDayIndex; i++) {
      days.push(null);
    }
    // Month days
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(i);
    }

    const weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

    return (
      <div className="card glass-panel mt-xl shadow-glow" style={{ padding: 'var(--space-md)' }}>
        <div className="flex justify-between items-center mb-md">
          <h3 className="card-title flex items-center gap-sm">
            <CalendarRange size={18} className="text-accent-cyan" /> Team Leave Calendar
          </h3>
          <div className="flex items-center gap-sm">
            <button className="btn btn-icon btn-secondary" onClick={handlePrevMonth} type="button">
              <ChevronLeft size={16} />
            </button>
            <span className="font-semibold text-white text-sm" style={{ minWidth: '120px', textAlign: 'center' }}>
              {monthNames[currentDate.getMonth()]} {year}
            </span>
            <button className="btn btn-icon btn-secondary" onClick={handleNextMonth} type="button">
              <ChevronRight size={16} />
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '8px', textAlign: 'center' }}>
          {weekdays.map(d => (
            <div key={d} className="font-semibold text-xs text-muted" style={{ paddingBottom: '8px' }}>{d}</div>
          ))}
          {days.map((day, idx) => {
            if (day === null) {
              return <div key={`empty-${idx}`} style={{ height: '76px', backgroundColor: 'rgba(255,255,255,0.01)', borderRadius: '8px' }}></div>;
            }

            const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayLeaves = teamLeaves.filter(l => l.start_date <= dateStr && l.end_date >= dateStr);
            const isToday = new Date().toDateString() === new Date(year, month - 1, day).toDateString();

            return (
              <div 
                key={day} 
                onClick={() => {
                  setFormData({
                    ...formData,
                    start_date: dateStr,
                    end_date: dateStr
                  });
                  setShowApplyModal(true);
                }}
                style={{ 
                  height: '76px', 
                  backgroundColor: isToday ? 'rgba(0, 240, 255, 0.05)' : 'rgba(255,255,255,0.02)', 
                  border: isToday ? '1px solid rgba(0, 240, 255, 0.3)' : '1px solid rgba(255,255,255,0.05)', 
                  borderRadius: '8px', 
                  padding: '6px', 
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'background 0.2s',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
                onMouseEnter={e => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)'}
                onMouseLeave={e => e.currentTarget.style.backgroundColor = isToday ? 'rgba(0, 240, 255, 0.05)' : 'rgba(255,255,255,0.02)'}
              >
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: isToday ? 'var(--accent-cyan)' : 'white' }}>{day}</span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', overflowY: 'auto', flex: 1, marginTop: '2px' }}>
                  {dayLeaves.map((l: any) => (
                    <div 
                      key={l.id} 
                      title={`${l.employee_name} (${l.leave_type})`}
                      style={{ 
                        fontSize: '0.6rem', 
                        backgroundColor: l.leave_type === 'sick' ? 'rgba(255, 61, 0, 0.15)' : 'rgba(0, 240, 255, 0.12)', 
                        color: l.leave_type === 'sick' ? 'var(--error)' : 'var(--accent-cyan)', 
                        padding: '1px 4px', 
                        borderRadius: '4px',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden'
                      }}
                    >
                      {l.employee_name.split(' ')[0]}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="animate-in stagger">
      <div className="page-header">
        <div>
          <h1 className="page-title text-transparent bg-clip-text bg-gradient-to-r from-white to-white/60">Leaves</h1>
          <p className="page-description">Manage your time off</p>
        </div>
        <button className="btn btn-primary shadow-glow" onClick={() => setShowApplyModal(true)}>
          <Plus size={18} /> Apply Leave
        </button>
      </div>

      {(user?.role === 'manager' || user?.role === 'hr_admin') && (
        <div className="tabs glass-tabs mb-xl">
          <button 
            className={`tab ${activeTab === 'my_leaves' ? 'active' : ''}`}
            onClick={() => setActiveTab('my_leaves')}
          >
            My Leaves
          </button>
          <button 
            className={`tab ${activeTab === 'team_queue' ? 'active' : ''}`}
            onClick={() => setActiveTab('team_queue')}
          >
            Team Queue <span className="ml-sm badge badge-pending" style={{ padding: '2px 6px' }}>{queue.length}</span>
          </button>
        </div>
      )}

      {activeTab === 'my_leaves' && (
        <>
          <div className="grid grid-3 mb-xl">
            {balances.map(b => (
              <div key={b.leave_type} className="card stat-card">
                <div className="stat-label uppercase tracking-widest text-xs">{b.leave_type} Leave</div>
                <div className="stat-value text-4xl my-xs">{b.available_days}</div>
                <div className="stat-trend text-muted">
                  {b.used_days} used out of {b.total_days}
                </div>
              </div>
            ))}
          </div>

          {renderCalendar()}

          <div className="card mt-xl">
            <div className="card-header">
              <h3 className="card-title flex items-center gap-sm"><CalendarRange size={18}/> Leave History</h3>
            </div>
            <div className="card-body p-0">
              {loading ? (
                <div className="p-xl text-center"><span className="spinner"></span></div>
              ) : history.length === 0 ? (
                <div className="empty-state py-2xl">
                  <Clock size={48} />
                  <div className="empty-state-title">No leaves taken yet</div>
                  <div className="empty-state-text">Your leave history will appear here.</div>
                </div>
              ) : (
                <table className="w-full">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Dates</th>
                      <th>Days</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map(l => (
                      <tr key={l.id}>
                        <td className="capitalize font-semibold">{l.leave_type}</td>
                        <td>{format(parseISO(l.start_date), 'MMM d, yyyy')} - {format(parseISO(l.end_date), 'MMM d, yyyy')}</td>
                        <td>{l.total_days}</td>
                        <td>{getStatusBadge(l.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </>
      )}

      {activeTab === 'team_queue' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Pending Approvals</h3>
          </div>
          <div className="card-body p-0">
            {queue.length === 0 ? (
              <div className="empty-state py-2xl">
                <Check size={48} className="text-success" />
                <div className="empty-state-title">All caught up</div>
                <div className="empty-state-text">No pending leave requests from your team.</div>
              </div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr>
                    <th>Employee</th>
                    <th>Type & Dates</th>
                    <th>Reason</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {queue.map(req => (
                    <tr key={req.id}>
                      <td>
                        <div className="font-semibold text-white">{req.employee_name}</div>
                      </td>
                      <td>
                        <div className="capitalize font-medium">{req.leave_type} ({req.total_days} days)</div>
                        <div className="text-xs text-muted">
                          {format(parseISO(req.start_date), 'MMM d')} - {format(parseISO(req.end_date), 'MMM d, yyyy')}
                        </div>
                      </td>
                      <td className="truncate max-w-[200px]">{req.reason || '-'}</td>
                      <td>
                        <div className="flex justify-end gap-sm">
                          <button 
                            className="btn btn-icon btn-secondary" 
                            style={{ color: 'var(--error)' }}
                            onClick={() => handleAction(req.id, 'reject')}
                            title="Reject"
                          >
                            <X size={16} />
                          </button>
                          <button 
                            className="btn btn-icon btn-primary"
                            onClick={() => handleAction(req.id, 'approve')}
                            title="Approve"
                          >
                            <Check size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {showApplyModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2 className="modal-title">Apply for Leave</h2>
              <button className="btn-icon" onClick={() => setShowApplyModal(false)}><X size={20}/></button>
            </div>
            <form onSubmit={handleApply}>
              <div className="modal-body">
                <div className="input-group">
                  <label className="input-label">Leave Type</label>
                  <select 
                    className="input capitalize" 
                    value={formData.leave_type}
                    onChange={e => setFormData({...formData, leave_type: e.target.value})}
                  >
                    {balances.map(b => (
                      <option key={b.leave_type} value={b.leave_type}>
                        {b.leave_type} ({b.available_days} available)
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-2">
                  <div className="input-group">
                    <label className="input-label">Start Date</label>
                    <input 
                      type="date" 
                      className="input" 
                      required
                      value={formData.start_date}
                      onChange={e => setFormData({...formData, start_date: e.target.value})}
                    />
                  </div>
                  <div className="input-group">
                    <label className="input-label">End Date</label>
                    <input 
                      type="date" 
                      className="input" 
                      required
                      value={formData.end_date}
                      onChange={e => setFormData({...formData, end_date: e.target.value})}
                    />
                  </div>
                </div>
                <div className="input-group">
                  <label className="input-label">Reason (Optional)</label>
                  <textarea 
                    className="input" 
                    placeholder="Brief reason for your leave..."
                    value={formData.reason}
                    onChange={e => setFormData({...formData, reason: e.target.value})}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-ghost" onClick={() => setShowApplyModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Submitting...' : 'Submit Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Leave;
