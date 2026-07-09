import React, { useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { format, parseISO } from 'date-fns';
import { ShieldAlert, Search, Terminal, Server, Clock } from 'lucide-react';

const Audit = () => {
  const { request, loading, error } = useApi();
  const [logs, setLogs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [actionFilter, setActionFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');

  const fetchLogs = async () => {
    try {
      let url = '/audit/logs?limit=50';
      if (actionFilter) url += `&action=${encodeURIComponent(actionFilter)}`;
      if (resourceFilter) url += `&resource_type=${encodeURIComponent(resourceFilter)}`;
      
      const res = await request(url);
      setLogs(res.logs || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter, resourceFilter, request]);

  return (
    <div className="animate-in stagger">
      <div className="page-header">
        <div>
          <h1 className="page-title text-transparent bg-clip-text bg-gradient-to-r from-white to-white/60">Audit Trail</h1>
          <p className="page-description">Security compliance and event logs</p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
          <div style={{ position: 'relative', width: '220px' }}>
            <Search style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', opacity: 0.5 }} size={16} />
            <input 
              type="text" 
              className="input" 
              style={{ width: '100%', paddingLeft: '36px' }}
              placeholder="Search Action..." 
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
            />
          </div>
          <select 
            className="input"
            style={{ width: '180px' }}
            value={resourceFilter}
            onChange={(e) => setResourceFilter(e.target.value)}
          >
            <option value="">All Resource Types</option>
            <option value="employee">Employee</option>
            <option value="document">Document</option>
            <option value="expense">Expense</option>
            <option value="leave_request">Leave Request</option>
            <option value="onboarding_run">Onboarding Run</option>
          </select>
        </div>
      </div>

      <div className="card glass-panel shadow-glow">
        <div className="card-header flex justify-between items-center">
          <h3 className="card-title flex items-center gap-sm">
            <Server size={18} className="text-accent" /> System Event Log ({total} total)
          </h3>
        </div>
        <div className="card-body p-0">
          {loading ? (
            <div className="p-xl text-center"><span className="spinner"></span></div>
          ) : error ? (
            <div className="empty-state py-2xl">
              <ShieldAlert size={48} style={{ color: 'var(--error)' }} />
              <div className="empty-state-title">Access Denied</div>
              <div className="empty-state-text">{error}</div>
            </div>
          ) : logs.length === 0 ? (
            <div className="empty-state py-2xl">
              <Terminal size={48} />
              <div className="empty-state-title">No events recorded</div>
              <div className="empty-state-text">Perform an action in the system to view logs.</div>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="w-full text-left">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Actor</th>
                    <th>Action</th>
                    <th>Resource</th>
                    <th>IP Address</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} style={{ transition: 'background 0.2s' }}>
                      <td className="whitespace-nowrap" style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.875rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Clock size={14} style={{ color: 'var(--accent-cyan)' }} />
                          {format(parseISO(log.created_at), 'MMM d, h:mm:ss a')}
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{
                            width: '24px', 
                            height: '24px', 
                            borderRadius: '50%', 
                            backgroundColor: 'rgba(255,255,255,0.05)', 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'center',
                            fontSize: '0.75rem',
                            fontWeight: 'bold',
                            border: '1px solid rgba(255,255,255,0.1)'
                          }}>
                            {log.actor_name.charAt(0)}
                          </div>
                          <span className="font-semibold text-white">{log.actor_name}</span>
                        </div>
                      </td>
                      <td className="font-mono text-xs" style={{ color: 'var(--accent-pink)' }}>
                        {log.action}
                      </td>
                      <td style={{ fontSize: '0.875rem' }}>
                        <span className="badge" style={{ backgroundColor: 'rgba(255,255,255,0.03)', color: 'rgba(255,255,255,0.8)', border: '1px solid rgba(255,255,255,0.05)' }}>
                          {log.resource_type}
                        </span>
                      </td>
                      <td className="font-mono text-xs text-muted">
                        {log.ip_address || '127.0.0.1'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Audit;
