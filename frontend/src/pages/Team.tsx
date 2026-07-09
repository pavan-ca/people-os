import React, { useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { format, parseISO } from 'date-fns';
import { Users, Search, Mail, Building2 } from 'lucide-react';

const Team = () => {
  const { request, loading } = useApi();
  const [employees, setEmployees] = useState<any[]>([]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetchEmployees = async () => {
      try {
        const res = await request('/employees');
        setEmployees(res);
      } catch (err) {
        console.error(err);
      }
    };
    fetchEmployees();
  }, [request]);

  const filtered = employees.filter(e => 
    e.name.toLowerCase().includes(search.toLowerCase()) || 
    e.job_title.toLowerCase().includes(search.toLowerCase()) ||
    (e.department?.name || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="animate-in stagger">
      <div className="page-header">
        <div>
          <h1 className="page-title text-transparent bg-clip-text bg-gradient-to-r from-white to-white/60">Directory</h1>
          <p className="page-description">Find people in your organization</p>
        </div>
        <div style={{ position: 'relative', width: '260px' }}>
          <Search style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', opacity: 0.5 }} className="text-muted" size={16} />
          <input 
            type="text" 
            className="input" 
            style={{ width: '100%', paddingLeft: '36px' }}
            placeholder="Search by name, role..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="grid grid-auto">
        {loading ? (
          <div className="col-span-full py-3xl text-center"><span className="spinner"></span></div>
        ) : filtered.length === 0 ? (
          <div className="col-span-full empty-state py-3xl">
            <Users size={48} className="text-muted/50 mb-md" />
            <div className="empty-state-title">No employees found</div>
          </div>
        ) : (
          filtered.map(emp => (
            <div key={emp.id} className="card glass-panel hover:bg-white/[0.03] transition-colors group cursor-pointer">
              <div className="card-body flex items-start gap-md">
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
                    fontSize: '1.25rem', 
                    fontWeight: 'bold', 
                    flexShrink: 0,
                    boxShadow: 'var(--shadow-glow)',
                    lineHeight: '1'
                  }} 
                  className="group-hover:scale-110 transition-transform"
                >
                  <span style={{ display: 'block', transform: 'translateY(1px)' }}>{emp.name.charAt(0)}</span>
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-bold text-white text-lg" style={{ margin: 0 }}>{emp.name}</h3>
                  <p className="text-sm font-medium" style={{ color: 'var(--accent-cyan)', margin: '2px 0 0 0', wordBreak: 'break-word' }}>{emp.job_title}</p>
                  
                  <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div className="flex items-center gap-xs text-xs text-muted" style={{ wordBreak: 'break-word' }}>
                      <Building2 size={14} style={{ flexShrink: 0 }} />
                      <span>{emp.department?.name || 'No Department'}</span>
                    </div>
                    <div className="flex items-center gap-xs text-xs text-muted" style={{ wordBreak: 'break-all' }}>
                      <Mail size={14} style={{ flexShrink: 0 }} />
                      <span>{emp.email}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Team;
