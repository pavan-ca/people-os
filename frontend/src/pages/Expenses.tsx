import React, { useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useAuth } from '../contexts/AuthContext';
import { format, parseISO } from 'date-fns';
import { Receipt, Plus, Check, X, CreditCard } from 'lucide-react';

const Expenses = () => {
  const { request, loading } = useApi();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'mine' | 'queue'>(
    (user?.role === 'manager' || user?.role === 'hr_admin') ? 'queue' : 'mine'
  );
  
  const [expenses, setExpenses] = useState<any[]>([]);
  const [queue, setQueue] = useState<any[]>([]);

  const [showApplyModal, setShowApplyModal] = useState(false);
  const [formData, setFormData] = useState({
    amount: '',
    currency: 'USD',
    category: 'travel',
    description: ''
  });

  const fetchData = async () => {
    try {
      if (activeTab === 'mine') {
        const res = await request('/expenses/mine');
        setExpenses(res);
      } else if (user?.role === 'manager' || user?.role === 'hr_admin') {
        const res = await request('/expenses/queue');
        setQueue(res);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeTab, request, user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = new FormData();
      data.append('amount', formData.amount);
      data.append('currency', formData.currency);
      data.append('category', formData.category);
      data.append('description', formData.description);

      await request('/expenses/submit', {
        method: 'POST',
        body: data
      });
      setShowApplyModal(false);
      setFormData({ amount: '', currency: 'USD', category: 'travel', description: '' });
      fetchData();
    } catch (err) {
      alert("Failed to submit expense");
    }
  };

  const handleAction = async (id: string, action: 'approve' | 'reject' | 'mark_paid') => {
    try {
      await request(`/expenses/${id}/action`, {
        method: 'POST',
        body: { action }
      });
      fetchData();
    } catch (err) {
      alert(`Failed to ${action} expense`);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved': return <span className="badge badge-approved">Approved</span>;
      case 'rejected': return <span className="badge badge-rejected">Rejected</span>;
      case 'paid': return <span className="badge badge-paid">Paid</span>;
      case 'with_manager': return <span className="badge badge-with_manager">With Manager</span>;
      case 'with_finance': return <span className="badge badge-with_finance">With Finance</span>;
      default: return <span className="badge badge-submitted">Submitted</span>;
    }
  };

  return (
    <div className="animate-in stagger">
      <div className="page-header">
        <div>
          <h1 className="page-title text-transparent bg-clip-text bg-gradient-to-r from-white to-white/60">Expenses</h1>
          <p className="page-description">Manage reimbursements and claims</p>
        </div>
        <button className="btn btn-primary shadow-glow-strong" onClick={() => setShowApplyModal(true)}>
          <Plus size={18} /> Submit Claim
        </button>
      </div>

      {(user?.role === 'manager' || user?.role === 'hr_admin') && (
        <div className="tabs glass-tabs mb-xl">
          <button 
            className={`tab ${activeTab === 'mine' ? 'active' : ''}`}
            onClick={() => setActiveTab('mine')}
          >
            My Claims
          </button>
          <button 
            className={`tab ${activeTab === 'queue' ? 'active' : ''}`}
            onClick={() => setActiveTab('queue')}
          >
            Team Queue <span className="ml-sm badge badge-pending">{queue.length}</span>
          </button>
        </div>
      )}

      {activeTab === 'mine' && (
        <div className="card glass-panel">
          <div className="card-body p-0">
            {loading ? (
              <div className="p-xl text-center"><span className="spinner"></span></div>
            ) : expenses.length === 0 ? (
              <div className="empty-state py-2xl">
                <Receipt size={48} className="text-muted/50 mb-md" />
                <div className="empty-state-title">No expenses submitted</div>
                <div className="empty-state-text">Your claims will appear here.</div>
              </div>
            ) : (
              <div className="table-wrapper">
                <table className="w-full text-left">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Category</th>
                      <th>Description</th>
                      <th>Amount</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {expenses.map(exp => (
                      <tr key={exp.id}>
                        <td className="whitespace-nowrap">{format(parseISO(exp.submitted_at), 'MMM d, yyyy')}</td>
                        <td className="capitalize font-medium text-white/90">{exp.category}</td>
                        <td className="truncate max-w-[250px]">{exp.description}</td>
                        <td className="font-bold text-white tracking-wide">
                          {exp.currency} {exp.amount.toFixed(2)}
                        </td>
                        <td>{getStatusBadge(exp.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'queue' && (
        <div className="card glass-panel">
          <div className="card-body p-0">
            {loading ? (
               <div className="p-xl text-center"><span className="spinner"></span></div>
            ) : queue.length === 0 ? (
              <div className="empty-state py-2xl">
                <Check size={48} className="text-success mb-md" />
                <div className="empty-state-title">Inbox Zero</div>
                <div className="empty-state-text">No pending expenses from your team.</div>
              </div>
            ) : (
              <div className="table-wrapper">
                <table className="w-full text-left">
                  <thead>
                    <tr>
                      <th>Employee</th>
                      <th>Category</th>
                      <th>Description</th>
                      <th>Amount</th>
                      <th className="text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {queue.map(req => (
                      <tr key={req.id}>
                        <td>
                          <div className="font-semibold text-white">{req.employee?.name || 'Unknown'}</div>
                          <div className="text-xs text-muted">{format(parseISO(req.submitted_at), 'MMM d, yyyy')}</div>
                        </td>
                        <td className="capitalize">{req.category}</td>
                        <td className="truncate max-w-[200px]">{req.description}</td>
                        <td className="font-bold text-white">
                          {req.currency} {req.amount.toFixed(2)}
                        </td>
                        <td>
                          <div className="flex justify-end gap-sm">
                            <button 
                              className="btn btn-icon btn-secondary hover:bg-error/20 hover:text-error hover:border-error/50 transition-colors" 
                              onClick={() => handleAction(req.id, 'reject')}
                              title="Reject"
                            >
                              <X size={16} />
                            </button>
                            <button 
                              className="btn btn-icon btn-primary shadow-glow"
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
              </div>
            )}
          </div>
        </div>
      )}

      {showApplyModal && (
        <div className="modal-overlay">
          <div className="modal glass-panel border-white/10">
            <div className="modal-header">
              <h2 className="modal-title font-bold text-white">Submit Expense</h2>
              <button className="btn-icon hover:bg-white/10" onClick={() => setShowApplyModal(false)}><X size={20}/></button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="grid grid-2">
                  <div className="input-group">
                    <label className="input-label">Amount</label>
                    <div style={{ position: 'relative' }}>
                      <div style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.4)', pointerEvents: 'none' }}>
                        <span>$</span>
                      </div>
                      <input 
                        type="number" 
                        step="0.01"
                        className="input w-full" 
                        style={{ paddingLeft: '32px' }}
                        required
                        value={formData.amount}
                        onChange={e => setFormData({...formData, amount: e.target.value})}
                      />
                    </div>
                  </div>
                  <div className="input-group">
                    <label className="input-label">Currency</label>
                    <select 
                      className="input" 
                      value={formData.currency}
                      onChange={e => setFormData({...formData, currency: e.target.value})}
                    >
                      <option value="USD">USD ($)</option>
                      <option value="EUR">EUR (€)</option>
                      <option value="GBP">GBP (£)</option>
                      <option value="INR">INR (₹)</option>
                    </select>
                  </div>
                </div>
                <div className="input-group">
                  <label className="input-label">Category</label>
                  <select 
                    className="input capitalize" 
                    value={formData.category}
                    onChange={e => setFormData({...formData, category: e.target.value})}
                  >
                    <option value="travel">Travel & Transit</option>
                    <option value="meals">Meals & Entertainment</option>
                    <option value="equipment">Office & Equipment</option>
                    <option value="training">Training & Education</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="input-group">
                  <label className="input-label">Description</label>
                  <textarea 
                    className="input" 
                    required
                    placeholder="E.g. Flight to client meeting..."
                    value={formData.description}
                    onChange={e => setFormData({...formData, description: e.target.value})}
                  />
                </div>
              </div>
              <div className="modal-footer border-t border-white/10 bg-black/20">
                <button type="button" className="btn btn-ghost" onClick={() => setShowApplyModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary shadow-glow" disabled={loading}>
                  {loading ? <span className="spinner"></span> : 'Submit Claim'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Expenses;
