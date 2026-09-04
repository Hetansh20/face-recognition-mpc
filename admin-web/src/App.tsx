import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { StudentsPage } from './pages/StudentsPage';
import { FacultyPage } from './pages/FacultyPage';
import { TimetablePage } from './pages/TimetablePage';
import { SessionsPage } from './pages/SessionsPage';
import { ReportsPage } from './pages/ReportsPage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { DevicesPage } from './pages/DevicesPage';

const ProtectedLayout: React.FC<{ title: string }> = ({ title }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 font-medium">
        Loading FaceAttend Portal...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-content">
        <Navbar title={title} />
        <main className="page-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<ProtectedLayout title="System Dashboard" />}>
            <Route path="/" element={<DashboardPage />} />
          </Route>

          <Route element={<ProtectedLayout title="Student Management" />}>
            <Route path="/students" element={<StudentsPage />} />
          </Route>

          <Route element={<ProtectedLayout title="Faculty Directory" />}>
            <Route path="/faculty" element={<FacultyPage />} />
          </Route>

          <Route element={<ProtectedLayout title="Timetable Scheduling" />}>
            <Route path="/timetable" element={<TimetablePage />} />
          </Route>

          <Route element={<ProtectedLayout title="Live Attendance & Sessions" />}>
            <Route path="/sessions" element={<SessionsPage />} />
          </Route>

          <Route element={<ProtectedLayout title="Attendance Reports" />}>
            <Route path="/reports" element={<ReportsPage />} />
          </Route>

          <Route element={<ProtectedLayout title="Security Audit & Logs" />}>
            <Route path="/logs" element={<AuditLogsPage />} />
          </Route>

          <Route element={<ProtectedLayout title="Registered Mobile Devices" />}>
            <Route path="/devices" element={<DevicesPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
