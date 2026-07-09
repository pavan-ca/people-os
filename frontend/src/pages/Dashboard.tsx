import React, { useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { DashboardData } from '../types';
import { format, parseISO } from 'date-fns';
import { 
  Briefcase, 
  CheckCircle2, 
  Clock, 
  FileText, 
  Users, 
  Wallet,
  ArrowRight,
  TrendingUp,
  AlertCircle,
  Target,
  Receipt
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const { request, loading, error } = useApi();
  const [data, setData] = useState<DashboardData | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const res = await request('/dashboard');
        setData(res);
      } catch (err) {
        console.error(err);
      }
    };
    fetchDashboard();
  }, [request]);

  if (loading || !data) {
    return <div className="loading-full"><span className="spinner"></span></div>;
  }

  if (error) {
    return <div className="empty-state">
      <AlertCircle />
      <h3 className="empty-state-title">Failed to load dashboard</h3>
      <p className="empty-state-text">{error}</p>
    </div>;
  }

  const renderEmployeeView = () => (
    <div className="stagger">
      <div className="grid grid-3 mb-xl">
        <div className="card stat-card">
          <div className="stat-icon cyan">
            <Clock />
          </div>
          <div className="stat-label">Pending Expenses</div>
          <div className="stat-value">{data.pending_expenses?.count || 0}</div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon violet">
            <FileText />
          </div>
          <div className="stat-label">Policies to Acknowledge</div>
          <div className="stat-value">{data.unacknowledged_policies || 0}</div>
        </div>
        {data.leave_balances?.[0] && (
          <div className="card stat-card">
            <div className="stat-icon amber">
              <Briefcase />
            </div>
            <div className="stat-label">{data.leave_balances[0].leave_type} Leave Balance</div>
            <div className="stat-value">{data.leave_balances[0].available_days} days</div>
          </div>
        )}
      </div>

      <div className="grid grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Leave Balances</h3>
          </div>
          <div className="card-body">
            <div className="flex-col gap-md">
              {data.leave_balances?.map((b) => (
                <div key={b.leave_type} className="flex justify-between items-center p-sm border-b" style={{ borderColor: 'var(--border)' }}>
                  <div>
                    <div className="font-semibold" style={{ textTransform: 'capitalize' }}>{b.leave_type}</div>
                    <div className="text-muted text-sm">{b.used_days} used / {b.total_days} total</div>
                  </div>
                  <div className="font-bold text-lg" style={{ color: 'var(--accent)' }}>
                    {b.available_days}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="card-footer">
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/leave')}>
              Apply Leave <ArrowRight size={16} />
            </button>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Upcoming Leaves</h3>
          </div>
          <div className="card-body">
            {data.upcoming_leaves && data.upcoming_leaves.length > 0 ? (
              <div className="flex-col gap-md">
                {data.upcoming_leaves.map((l) => (
                  <div key={l.id} className="flex justify-between items-center p-sm border-b" style={{ borderColor: 'var(--border)' }}>
                    <div>
                      <div className="font-semibold" style={{ textTransform: 'capitalize' }}>{l.leave_type} Leave</div>
                      <div className="text-muted text-sm">
                        {format(parseISO(l.start_date), 'MMM d, yyyy')} - {format(parseISO(l.end_date), 'MMM d, yyyy')}
                      </div>
                    </div>
                    <span className="badge badge-approved">{l.total_days} days</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state py-lg">
                <p className="text-muted text-sm">No upcoming leaves scheduled.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const renderNewHireView = () => (
    <div className="stagger">
      <div className="card mb-xl overflow-hidden" style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(6,182,212,0.1) 100%)', borderColor: 'var(--accent)' }}>
        <div className="card-body flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-xs" style={{ color: 'white' }}>Welcome to PeopleOS, {data.name.split(' ')[0]}!</h2>
            <p className="text-muted">We're so glad you're here. Let's get you set up.</p>
            
            {data.onboarding && (
              <div className="mt-lg">
                <div className="flex justify-between mb-xs text-sm font-semibold">
                  <span>Onboarding Progress</span>
                  <span>{data.onboarding.progress_pct}%</span>
                </div>
                <div className="progress-bar-track w-64">
                  <div className="progress-bar-fill" style={{ width: `${data.onboarding.progress_pct}%` }}></div>
                </div>
              </div>
            )}
          </div>
          <div className="hidden md:block">
            <div style={{ width: '96px', height: '96px', borderRadius: '50%', backgroundColor: 'rgba(0, 240, 255, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2.5rem', boxShadow: 'var(--shadow-glow)' }}>
              🎉
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title flex items-center gap-sm">
              <Target size={18} className="text-accent" /> Up Next
            </h3>
          </div>
          <div className="card-body">
            {data.onboarding?.next_task ? (
              <div className="flex-col gap-sm">
                <div className="text-sm text-muted">Step {data.onboarding.next_task.step_index}</div>
                <div className="text-lg font-semibold">{data.onboarding.next_task.title}</div>
                <button className="btn btn-primary mt-md w-max" onClick={() => navigate('/onboarding')}>
                  Complete Task
                </button>
              </div>
            ) : (
              <div className="text-center py-xl">
                <CheckCircle2 size={48} className="text-success mx-auto mb-sm" />
                <div className="font-semibold text-lg">All caught up!</div>
                <div className="text-muted text-sm">You've completed all onboarding tasks.</div>
              </div>
            )}
          </div>
        </div>

        {/* Can reuse parts of employee view here too, but focused on new hire actions */}
      </div>
    </div>
  );

  const renderManagerView = () => (
    <div className="stagger">
      <div className="grid grid-4 mb-xl">
        <div className="card stat-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/leave')}>
          <div className="stat-icon rose">
            <Clock />
          </div>
          <div className="stat-label">Leave Requests</div>
          <div className="stat-value">{data.pending_leave_approvals || 0}</div>
          <div className="stat-trend">Needs your approval</div>
        </div>
        <div className="card stat-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/expenses')}>
          <div className="stat-icon amber">
            <Receipt />
          </div>
          <div className="stat-label">Expense Claims</div>
          <div className="stat-value">{data.pending_expense_approvals || 0}</div>
          <div className="stat-trend">Needs your approval</div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon cyan">
            <Users />
          </div>
          <div className="stat-label">Direct Reports</div>
          <div className="stat-value">{data.direct_reports_count || 0}</div>
        </div>
        <div className="card stat-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/onboarding')}>
          <div className="stat-icon violet">
            <Target />
          </div>
          <div className="stat-label">Delayed Onboarding</div>
          <div className="stat-value">{data.delayed_onboarding_count || 0}</div>
          <div className="stat-trend">In your team</div>
        </div>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Team on Leave This Week</h3>
          </div>
          <div className="card-body">
            {data.team_on_leave_this_week && data.team_on_leave_this_week.length > 0 ? (
              <div className="flex-col gap-md">
                {data.team_on_leave_this_week.map((l, i) => (
                  <div key={i} className="flex justify-between items-center p-sm border-b" style={{ borderColor: 'var(--border)' }}>
                    <div className="flex items-center gap-sm">
                      <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: 'rgba(112,0,255,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.875rem', fontWeight: 'bold', color: 'var(--accent-cyan)', border: '1px solid rgba(0, 240, 255, 0.2)' }}>
                        {l.employee_name.charAt(0)}
                      </div>
                      <div>
                        <div className="font-semibold">{l.employee_name}</div>
                        <div className="text-muted text-xs" style={{ textTransform: 'capitalize' }}>{l.leave_type} Leave</div>
                      </div>
                    </div>
                    <div className="text-right text-sm">
                      <div>{format(parseISO(l.start_date), 'MMM d')} - {format(parseISO(l.end_date), 'MMM d')}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state py-lg">
                <p className="text-muted text-sm">No one is on leave this week.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const renderHRAdminView = () => (
    <div className="stagger">
      <div className="grid grid-4 mb-xl">
        <div className="card stat-card">
          <div className="stat-icon violet">
            <Users />
          </div>
          <div className="stat-label">Total Employees</div>
          <div className="stat-value">{data.total_active_employees || 0}</div>
          <div className="stat-trend up"><TrendingUp size={14}/> +{data.new_hires_last_30_days} this month</div>
        </div>
        <div className="card stat-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/onboarding')}>
          <div className="stat-icon cyan">
            <Target />
          </div>
          <div className="stat-label">Active Onboarding</div>
          <div className="stat-value">{data.active_onboarding_runs || 0}</div>
          <div className="stat-trend down">{data.delayed_onboarding_runs} delayed</div>
        </div>
        <div className="card stat-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/leave')}>
          <div className="stat-icon amber">
            <Clock />
          </div>
          <div className="stat-label">Pending Leaves</div>
          <div className="stat-value">{data.pending_leave_requests || 0}</div>
          <div className="stat-trend">Company wide</div>
        </div>
        <div className="card stat-card" style={{ cursor: 'pointer' }} onClick={() => navigate('/expenses')}>
          <div className="stat-icon emerald">
            <Wallet />
          </div>
          <div className="stat-label">Pending Expenses</div>
          <div className="stat-value">{data.pending_expense_claims || 0}</div>
          <div className="stat-trend">Awaiting manager/finance</div>
        </div>
      </div>

      <div className="grid grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Recent Hires</h3>
          </div>
          <div className="card-body p-0">
            <table className="w-full">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Join Date</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_hires?.map((h) => (
                  <tr key={h.id}>
                    <td>
                      <div className="font-semibold text-white">{h.name}</div>
                      <div className="text-xs text-muted">{h.department || '-'}</div>
                    </td>
                    <td>{h.job_title}</td>
                    <td>{h.join_date ? format(parseISO(h.join_date), 'MMM d, yyyy') : '-'}</td>
                  </tr>
                ))}
                {!data.recent_hires?.length && (
                  <tr>
                    <td colSpan={3} className="text-center py-lg text-muted">No recent hires</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="animate-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-description">Overview for {format(new Date(data.today), 'EEEE, MMMM do, yyyy')}</p>
        </div>
      </div>
      
      {data.view === 'new_hire' && renderNewHireView()}
      {data.view === 'employee' && renderEmployeeView()}
      {data.view === 'manager' && renderManagerView()}
      {data.view === 'hr_admin' && renderHRAdminView()}
    </div>
  );
};

export default Dashboard;
