import React, { useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useAuth } from '../contexts/AuthContext';
import { format, parseISO } from 'date-fns';
import { Target, CheckCircle2, Play, AlertCircle, Users, Check, Clock } from 'lucide-react';

const Onboarding = () => {
  const { request, loading } = useApi();
  const { user } = useAuth();
  const [run, setRun] = useState<any>(null); // For employees
  const [runs, setRuns] = useState<any[]>([]); // For managers/admins
  const [expandedRun, setExpandedRun] = useState<string | null>(null);

  const fetchOnboarding = async () => {
    try {
      if (user?.role === 'employee') {
        const res = await request('/onboarding/runs/mine');
        if (res && res.length > 0) {
          setRun(res[0]);
        } else {
          setRun(null);
        }
      } else if (user?.role === 'hr_admin' || user?.role === 'manager') {
        const endpoint = user.role === 'hr_admin' ? '/onboarding/runs/all' : '/onboarding/runs/team';
        const res = await request(endpoint);
        setRuns(res || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (user) {
      fetchOnboarding();
    }
  }, [request, user]);

  const handleCompleteTask = async (taskId: string) => {
    try {
      await request(`/onboarding/tasks/${taskId}/complete`, { 
        method: 'POST',
        body: { notes: 'Completed via onboarding pipeline' }
      });
      fetchOnboarding();
    } catch (err) {
      alert("Failed to complete task");
    }
  };

  if (loading && !run && runs.length === 0) {
    return <div className="loading-full"><span className="spinner"></span></div>;
  }

  // RENDER PIPELINE VIEW (HR Admin / Manager)
  if (user?.role === 'hr_admin' || user?.role === 'manager') {
    return (
      <div className="animate-in stagger">
        <div className="page-header border-b pb-xl" style={{ borderColor: 'var(--border)' }}>
          <div>
            <div className="flex items-center gap-sm text-accent mb-sm">
              <Users size={20} /> <span className="font-semibold uppercase tracking-wider text-sm">Management</span>
            </div>
            <h1 className="page-title">Onboarding Pipeline</h1>
            <p className="page-description mt-xs">
              {user.role === 'hr_admin' 
                ? 'Monitor and complete tasks across all active new hire onboarding workflows.' 
                : 'Track onboarding checklists for your direct reports.'}
            </p>
          </div>
        </div>

        <div className="grid grid-2 mt-xl">
          {runs.length === 0 ? (
            <div className="col-span-full empty-state py-3xl card glass-panel">
              <CheckCircle2 size={48} className="text-success mb-md" />
              <div className="empty-state-title">No active onboarding runs</div>
              <div className="empty-state-text">All employee checklists are completed or closed.</div>
            </div>
          ) : (
            runs.map((r: any) => {
              const isExpanded = expandedRun === r.id;
              return (
                <div key={r.id} className="card glass-panel" style={{ height: 'fit-content' }}>
                  <div className="card-header" style={{ cursor: 'pointer' }} onClick={() => setExpandedRun(isExpanded ? null : r.id)}>
                    <div className="flex justify-between items-center">
                      <div>
                        <h3 className="font-bold text-lg text-white" style={{ margin: 0 }}>{r.employee_name}</h3>
                        <p className="text-xs text-muted" style={{ marginTop: '2px' }}>{r.template_name || 'Generic Workflow'}</p>
                      </div>
                      <div className="text-right">
                        <span className="font-bold text-accent-cyan" style={{ fontSize: '1.25rem' }}>{r.progress_pct}%</span>
                        <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', fontWeight: 600 }}>Progress</div>
                      </div>
                    </div>
                    <div className="progress-bar-track" style={{ marginTop: 'var(--space-sm)' }}>
                      <div className="progress-bar-fill" style={{ width: `${r.progress_pct}%` }}></div>
                    </div>
                  </div>
                  
                  {isExpanded && (
                    <div className="card-body" style={{ padding: 'var(--space-md)', display: 'flex', flexDirection: 'column', gap: 'var(--space-md)', backgroundColor: 'rgba(0,0,0,0.1)' }}>
                      <h4 className="text-xs uppercase tracking-widest text-muted" style={{ fontWeight: 700 }}>Task Checklist</h4>
                      {r.tasks.map((task: any) => {
                        const isTaskCompleted = task.status === 'completed' || task.status === 'skipped';
                        const isTaskInProgress = task.status === 'in_progress';
                        const canComplete = isTaskInProgress && (task.owner_id === user.id || user.role === 'hr_admin');

                        return (
                          <div key={task.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', borderRadius: '8px', backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
                            <div style={{ opacity: isTaskCompleted ? 0.5 : 1 }}>
                              <div className="font-semibold text-white text-sm" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                {isTaskCompleted ? <CheckCircle2 size={16} style={{ color: 'var(--success)' }} /> : <Clock size={16} style={{ color: isTaskInProgress ? 'var(--accent-cyan)' : 'var(--text-tertiary)' }} />}
                                {task.title}
                              </div>
                              <span style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)', marginLeft: '22px' }}>
                                Assigned to: {task.owner_role === 'employee' ? 'New Hire' : task.owner_role === 'manager' ? 'Manager' : 'HR / IT'}
                              </span>
                            </div>
                            
                            {canComplete && (
                              <button 
                                onClick={() => handleCompleteTask(task.id)}
                                className="btn btn-sm btn-primary shadow-glow"
                              >
                                <Check size={14} /> Complete
                              </button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    );
  }

  // RENDER NEW HIRE VIEW (Employee)
  if (!run) {
    return (
      <div className="empty-state py-3xl animate-in">
        <CheckCircle2 size={64} style={{ color: 'var(--success)' }} />
        <h2 className="text-2xl font-bold text-white mb-sm">You're all set!</h2>
        <p className="text-muted">You have no active onboarding checklists.</p>
      </div>
    );
  }

  const tasks = run.tasks || [];
  const completed = tasks.filter((t: any) => t.status === 'completed' || t.status === 'skipped').length;
  const progress = tasks.length > 0 ? Math.round((completed / tasks.length) * 100) : 0;

  return (
    <div className="animate-in stagger max-w-3xl mx-auto">
      <div className="page-header flex items-end justify-between border-b pb-xl" style={{ borderColor: 'var(--border)' }}>
        <div>
          <div className="flex items-center gap-sm text-accent mb-sm">
            <Target size={20} /> <span className="font-semibold uppercase tracking-wider text-sm">Onboarding</span>
          </div>
          <h1 className="page-title">{run.template_name || 'Onboarding Checklist'}</h1>
          <p className="page-description mt-xs">Let's get you set up for success at PeopleOS.</p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-white">{progress}%</div>
          <div className="text-xs text-muted uppercase tracking-widest font-semibold mt-1">Complete</div>
        </div>
      </div>

      <div className="mt-xl">
        <div className="card p-xl bg-surface/50 border-none shadow-none">
          {tasks.map((task: any, idx: number) => {
            const isCompleted = task.status === 'completed' || task.status === 'skipped';
            const isInProgress = task.status === 'in_progress';
            const isPending = task.status === 'pending';
            
            return (
              <div 
                key={task.id} 
                style={{ 
                  display: 'flex', 
                  alignItems: 'flex-start', 
                  gap: 'var(--space-xl)', 
                  paddingBottom: 'var(--space-2xl)', 
                  position: 'relative' 
                }}
                className={isCompleted ? 'completed' : isInProgress ? 'in_progress' : 'pending'}
              >
                {/* Connecting line */}
                {idx !== tasks.length - 1 && (
                  <div style={{
                    position: 'absolute',
                    left: '24px',
                    top: '48px',
                    bottom: '0',
                    width: '2px',
                    backgroundColor: 'rgba(255,255,255,0.1)',
                    transform: 'translateX(-50%)'
                  }}></div>
                )}
                
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  border: '2px solid rgba(255,255,255,0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  fontSize: '1.125rem',
                  flexShrink: 0,
                  zIndex: 10,
                  backgroundColor: '#000',
                  boxShadow: '0 0 20px rgba(0,0,0,0.5)'
                }}>
                  {isCompleted ? <CheckCircle2 size={24} style={{ color: 'var(--success)' }} /> : task.step_index}
                </div>
                
                <div style={{ flex: 1, paddingTop: '4px', opacity: isCompleted ? 0.5 : 1 }}>
                  <h3 className="font-bold text-xl text-white tracking-tight" style={{ marginBottom: '4px' }}>{task.title}</h3>
                  <p className="text-sm" style={{ color: 'rgba(255,255,255,0.5)' }}>
                    Assigned to: <span className="uppercase font-semibold tracking-widest" style={{ color: 'rgba(255,255,255,0.7)' }}>
                      {task.owner_id === run.employee_id ? 'You' : 'HR / IT'}
                    </span>
                  </p>
                  
                  {isInProgress && (
                    <div className="rounded-2xl shadow-glow glass-panel" style={{ 
                      marginTop: 'var(--space-lg)', 
                      padding: 'var(--space-lg)', 
                      border: '1px solid rgba(0, 240, 255, 0.3)', 
                      backgroundColor: 'rgba(0, 240, 255, 0.05)' 
                    }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                        <div>
                          <span style={{ 
                            display: 'block', 
                            fontSize: '0.75rem', 
                            fontWeight: 'bold', 
                            textTransform: 'uppercase', 
                            letterSpacing: '0.1em', 
                            color: 'var(--accent-cyan)', 
                            marginBottom: '8px' 
                          }}>
                            Current Action
                          </span>
                          <span style={{ fontSize: '0.875rem', color: 'rgba(255,255,255,0.9)' }}>
                            {task.owner_id === run.employee_id 
                              ? 'Please complete this requirement to unlock the next step in your onboarding journey.' 
                              : 'HR / IT is currently working on this step. You will be notified when it is complete.'}
                          </span>
                        </div>
                        
                        {task.owner_id === run.employee_id ? (
                          <div>
                            <button 
                              className="btn btn-primary btn-lg shadow-glow-strong"
                              onClick={() => handleCompleteTask(task.id)}
                            >
                              <CheckCircle2 size={20} /> Mark Complete
                            </button>
                          </div>
                        ) : (
                          <div>
                            <div className="btn btn-lg" style={{ 
                              backgroundColor: 'rgba(255,255,255,0.05)', 
                              color: 'rgba(255,255,255,0.5)', 
                              cursor: 'not-allowed',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '8px'
                            }}>
                              <span className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></span> 
                              Waiting for HR...
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {isPending && task.depends_on && task.depends_on.length > 0 && (
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px', 
                      marginTop: 'var(--space-md)', 
                      padding: '8px 16px', 
                      borderRadius: '8px', 
                      backgroundColor: 'rgba(255,255,255,0.05)', 
                      border: '1px solid rgba(255,255,255,0.1)', 
                      fontSize: '0.875rem', 
                      color: 'rgba(255,255,255,0.5)', 
                      width: 'max-content' 
                    }}>
                      <AlertCircle size={16} style={{ color: 'var(--warning)' }} /> 
                      <span style={{ fontWeight: 500 }}>Locked until previous step is completed</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
