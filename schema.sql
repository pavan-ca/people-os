-- ============================================================
-- PeopleOS — Full Database Schema
-- Run: psql -U postgres -d peopleos -f schema.sql
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- DEPARTMENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS departments (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(120) NOT NULL UNIQUE,
    head_employee_id UUID,         -- FK set after employees table
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- EMPLOYEES
-- ============================================================
CREATE TABLE IF NOT EXISTS employees (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(200) NOT NULL,
    email               VARCHAR(255) NOT NULL UNIQUE,
    password_hash       TEXT NOT NULL,
    role                VARCHAR(20)  NOT NULL CHECK (role IN ('employee','manager','hr_admin')),
    department_id       UUID REFERENCES departments(id) ON DELETE SET NULL,
    manager_id          UUID REFERENCES employees(id) ON DELETE SET NULL,
    job_title           VARCHAR(150),
    phone               VARCHAR(30),
    avatar_url          TEXT,
    join_date           DATE NOT NULL DEFAULT CURRENT_DATE,
    employment_status   VARCHAR(30) NOT NULL DEFAULT 'active' CHECK (employment_status IN ('active','inactive','on_leave','terminated')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Now set FK on departments
ALTER TABLE departments
    ADD CONSTRAINT fk_departments_head
    FOREIGN KEY (head_employee_id) REFERENCES employees(id) ON DELETE SET NULL
    DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX IF NOT EXISTS idx_employees_email      ON employees(email);
CREATE INDEX IF NOT EXISTS idx_employees_role       ON employees(role);
CREATE INDEX IF NOT EXISTS idx_employees_dept       ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_employees_manager    ON employees(manager_id);
CREATE INDEX IF NOT EXISTS idx_employees_name_trgm  ON employees USING GIN (name gin_trgm_ops);

-- ============================================================
-- LEAVE BALANCES
-- ============================================================
CREATE TABLE IF NOT EXISTS leave_balances (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    leave_type  VARCHAR(50) NOT NULL CHECK (leave_type IN ('casual','earned','sick','annual','maternity','paternity','unpaid')),
    total_days  NUMERIC(5,1) NOT NULL DEFAULT 0,
    used_days   NUMERIC(5,1) NOT NULL DEFAULT 0,
    pending_days NUMERIC(5,1) NOT NULL DEFAULT 0,
    carry_forward NUMERIC(5,1) NOT NULL DEFAULT 0,
    year        INTEGER NOT NULL DEFAULT EXTRACT(YEAR FROM CURRENT_DATE),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (employee_id, leave_type, year)
);

CREATE INDEX IF NOT EXISTS idx_leave_bal_emp ON leave_balances(employee_id);

-- ============================================================
-- LEAVE REQUESTS
-- ============================================================
CREATE TABLE IF NOT EXISTS leave_requests (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    leave_type  VARCHAR(50) NOT NULL CHECK (leave_type IN ('casual','earned','sick','annual','maternity','paternity','unpaid')),
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    total_days  NUMERIC(5,1) NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','cancelled')),
    approver_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    reason      TEXT,
    note        TEXT,                -- approver note on rejection
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    CONSTRAINT chk_dates CHECK (end_date >= start_date)
);

CREATE INDEX IF NOT EXISTS idx_leave_req_emp    ON leave_requests(employee_id);
CREATE INDEX IF NOT EXISTS idx_leave_req_status ON leave_requests(status);
CREATE INDEX IF NOT EXISTS idx_leave_req_dates  ON leave_requests(start_date, end_date);

-- ============================================================
-- ONBOARDING TEMPLATES
-- ============================================================
CREATE TABLE IF NOT EXISTS onboarding_templates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(200) NOT NULL,
    role_target     VARCHAR(20) CHECK (role_target IN ('employee','manager','hr_admin')),
    department_id   UUID REFERENCES departments(id) ON DELETE SET NULL,
    employment_type VARCHAR(30) DEFAULT 'full_time',
    steps           JSONB NOT NULL DEFAULT '[]',
    -- Each step: {index, title, description, owner_role, depends_on[], deadline_days}
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_by      UUID REFERENCES employees(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- ONBOARDING RUNS (per employee)
-- ============================================================
CREATE TABLE IF NOT EXISTS onboarding_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    template_id     UUID NOT NULL REFERENCES onboarding_templates(id) ON DELETE RESTRICT,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    status          VARCHAR(20) NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress','completed','delayed','cancelled')),
    due_date        DATE,
    UNIQUE (employee_id, template_id)
);

CREATE INDEX IF NOT EXISTS idx_onboarding_runs_emp    ON onboarding_runs(employee_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_runs_status ON onboarding_runs(status);

-- ============================================================
-- ONBOARDING TASKS (per run step)
-- ============================================================
CREATE TABLE IF NOT EXISTS onboarding_tasks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id          UUID NOT NULL REFERENCES onboarding_runs(id) ON DELETE CASCADE,
    step_index      INTEGER NOT NULL,
    title           VARCHAR(300) NOT NULL,
    description     TEXT,
    owner_id        UUID REFERENCES employees(id) ON DELETE SET NULL,
    owner_role      VARCHAR(20),
    depends_on      INTEGER[],           -- step indexes this task depends on
    deadline_days   INTEGER,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','in_progress','completed','skipped','blocked')),
    completed_at    TIMESTAMPTZ,
    due_date        DATE,
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_onboarding_tasks_run    ON onboarding_tasks(run_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_tasks_owner  ON onboarding_tasks(owner_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_tasks_status ON onboarding_tasks(status);

-- ============================================================
-- DOCUMENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id        UUID REFERENCES employees(id) ON DELETE CASCADE,  -- NULL = company-wide
    doc_type        VARCHAR(50) NOT NULL CHECK (doc_type IN (
                        'payslip','offer_letter','appraisal','tax_form',
                        'policy','handbook','compliance','other'
                    )),
    title           VARCHAR(300) NOT NULL,
    description     TEXT,
    version         INTEGER NOT NULL DEFAULT 1,
    storage_url     TEXT NOT NULL,
    file_name       TEXT NOT NULL,
    file_size       BIGINT,
    mime_type       VARCHAR(100),
    uploaded_by     UUID NOT NULL REFERENCES employees(id) ON DELETE RESTRICT,
    visible_to_roles TEXT[] NOT NULL DEFAULT ARRAY['employee','manager','hr_admin'],
    is_company_wide BOOLEAN NOT NULL DEFAULT FALSE,
    requires_ack    BOOLEAN NOT NULL DEFAULT FALSE,
    changelog       TEXT,               -- what changed in this version
    parent_doc_id   UUID REFERENCES documents(id) ON DELETE SET NULL,  -- previous version
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_owner      ON documents(owner_id);
CREATE INDEX IF NOT EXISTS idx_documents_type       ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_company    ON documents(is_company_wide);

-- Full-text search on title+description
ALTER TABLE documents ADD COLUMN IF NOT EXISTS search_vector TSVECTOR
    GENERATED ALWAYS AS (to_tsvector('english', coalesce(title,'') || ' ' || coalesce(description,''))) STORED;
CREATE INDEX IF NOT EXISTS idx_documents_fts ON documents USING GIN(search_vector);

-- ============================================================
-- DOCUMENT ACKNOWLEDGEMENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS document_acknowledgements (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    acknowledged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, employee_id)
);

-- ============================================================
-- EXPENSES
-- ============================================================
CREATE TABLE IF NOT EXISTS expenses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id     UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    amount          NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    currency        VARCHAR(5) NOT NULL DEFAULT 'INR',
    category        VARCHAR(50) NOT NULL CHECK (category IN (
                        'travel','accommodation','meals','equipment',
                        'software','training','medical','other'
                    )),
    description     TEXT NOT NULL,
    receipt_url     TEXT,
    receipt_filename TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'submitted' CHECK (status IN (
                        'submitted','with_manager','with_finance','approved','rejected','paid'
                    )),
    approver_id     UUID REFERENCES employees(id) ON DELETE SET NULL,
    finance_admin_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    submitted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ,
    rejection_note  TEXT,
    payment_date    DATE,
    payment_ref     VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_expenses_emp    ON expenses(employee_id);
CREATE INDEX IF NOT EXISTS idx_expenses_status ON expenses(status);
CREATE INDEX IF NOT EXISTS idx_expenses_approver ON expenses(approver_id);

-- ============================================================
-- NOTIFICATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipient_id    UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    type            VARCHAR(50) NOT NULL,
    title           VARCHAR(300) NOT NULL,
    body            TEXT,
    link            TEXT,
    read            BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read      ON notifications(recipient_id, read);

-- ============================================================
-- AUDIT LOGS
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id        UUID REFERENCES employees(id) ON DELETE SET NULL,
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(50) NOT NULL,
    resource_id     UUID,
    metadata        JSONB DEFAULT '{}',
    ip_address      VARCHAR(45),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_actor    ON audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_created  ON audit_logs(created_at DESC);

-- ============================================================
-- FUNCTION: updated_at auto-update
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE OR REPLACE TRIGGER trg_onboarding_templates_updated_at
    BEFORE UPDATE ON onboarding_templates
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
