export interface Employee {
  id: string;
  name: string;
  email: string;
  role: 'employee' | 'manager' | 'hr_admin';
  job_title: string;
  department: string | null;
  join_date: string | null;
}

export interface DashboardData {
  employee_id: string;
  name: string;
  role: string;
  job_title: string;
  department: string | null;
  join_date: string | null;
  unread_notifications: number;
  today: string;
  view: 'employee' | 'new_hire' | 'manager' | 'hr_admin';
  // Employee/New Hire fields
  is_new_hire?: boolean;
  onboarding?: {
    run_id: string;
    progress_pct: number;
    total_tasks: number;
    completed_tasks: number;
    due_date: string | null;
    next_task: {
      id: string;
      title: string;
      step_index: number;
    } | null;
  } | null;
  leave_balances?: Array<{
    leave_type: string;
    total_days: number;
    used_days: number;
    pending_days: number;
    available_days: number;
  }>;
  upcoming_leaves?: Array<{
    id: string;
    leave_type: string;
    start_date: string;
    end_date: string;
    total_days: number;
  }>;
  pending_expenses?: { count: number };
  unacknowledged_policies?: number;
  
  // Manager fields
  pending_leave_approvals?: number;
  pending_expense_approvals?: number;
  direct_reports_count?: number;
  team_on_leave_this_week?: Array<any>;
  delayed_onboarding_count?: number;
  my_leave_balances?: Array<any>;
  my_upcoming_leaves?: Array<any>;

  // HR Admin fields
  total_active_employees?: number;
  new_hires_last_30_days?: number;
  active_onboarding_runs?: number;
  delayed_onboarding_runs?: number;
  pending_leave_requests?: number;
  pending_expense_claims?: number;
  policies_requiring_acknowledgement?: number;
  recent_hires?: Array<any>;
}
