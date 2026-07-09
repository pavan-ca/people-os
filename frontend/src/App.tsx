import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Leave from './pages/Leave';
import Onboarding from './pages/Onboarding';
import Documents from './pages/Documents';
import Expenses from './pages/Expenses';
import Team from './pages/Team';
import Audit from './pages/Audit';

const ProtectedRoute = ({ children, allowedRoles }: { children: React.ReactNode, allowedRoles?: string[] }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <div className="login-page"><span className="spinner"></span></div>;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="leave" element={<Leave />} />
          <Route path="expenses" element={<Expenses />} />
          <Route path="documents" element={<Documents />} />
          <Route path="onboarding" element={<Onboarding />} />
          <Route 
            path="team" 
            element={
              <ProtectedRoute allowedRoles={['manager', 'hr_admin']}>
                <Team />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="audit" 
            element={
              <ProtectedRoute allowedRoles={['hr_admin']}>
                <Audit />
              </ProtectedRoute>
            } 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;

