import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Users, UserCheck, Calendar, Clock,
  FileSpreadsheet, ShieldAlert, Smartphone, LogOut, Camera, Sparkles
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/students', label: 'Students', icon: Users },
    { path: '/faculty', label: 'Faculty Directory', icon: UserCheck },
    { path: '/timetable', label: 'Timetable Scheduling', icon: Calendar },
    { path: '/sessions', label: 'Live Sessions', icon: Clock },
    { path: '/reports', label: 'Attendance Reports', icon: FileSpreadsheet },
    { path: '/logs', label: 'Audit & System Logs', icon: ShieldAlert },
    { path: '/devices', label: 'Mobile Devices', icon: Smartphone },
  ];

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div style={{
        padding: '1.5rem 1.5rem',
        borderBottom: '1px solid var(--border-card)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.875rem'
      }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '0.875rem',
          background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 20px rgba(99, 102, 241, 0.4)',
          position: 'relative'
        }}>
          <Camera style={{ width: '22px', height: '22px', color: '#ffffff' }} />
          <Sparkles style={{ width: '12px', height: '12px', color: '#fbbf24', position: 'absolute', top: '-4px', right: '-4px' }} />
        </div>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff', lineHeight: 1.1, letterSpacing: '-0.02em' }}>
            FaceAttend
          </h2>
          <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: '#818cf8', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            ENTERPRISE v1.0
          </span>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav style={{ padding: '1rem 0.75rem', flex: 1, display: 'flex', flexDirection: 'column', gap: '0.375rem', overflowY: 'auto' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                gap: '0.875rem',
                padding: '0.75rem 1rem',
                borderRadius: '0.75rem',
                color: isActive ? '#ffffff' : 'var(--text-muted)',
                background: isActive ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.22) 0%, rgba(168, 85, 247, 0.15) 100%)' : 'transparent',
                border: isActive ? '1px solid rgba(99, 102, 241, 0.35)' : '1px solid transparent',
                fontWeight: isActive ? 600 : 400,
                fontSize: '0.875rem',
                textDecoration: 'none',
                transition: 'all 0.2s ease',
                boxShadow: isActive ? '0 4px 15px rgba(99, 102, 241, 0.15)' : 'none'
              })}
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span style={{
                      position: 'absolute',
                      left: '0',
                      top: '20%',
                      bottom: '20%',
                      width: '4px',
                      borderRadius: '0 4px 4px 0',
                      background: 'linear-gradient(180deg, #6366f1 0%, #a855f7 100%)'
                    }} />
                  )}
                  <Icon style={{
                    width: '19px',
                    height: '19px',
                    color: isActive ? '#818cf8' : 'var(--text-dim)',
                    transition: 'color 0.2s ease'
                  }} />
                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* User Profile Footer Card */}
      <div style={{
        padding: '1rem',
        borderTop: '1px solid var(--border-card)',
        background: 'rgba(10, 15, 30, 0.6)',
        backdropFilter: 'blur(10px)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '0.75rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', overflow: 'hidden' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(168, 85, 247, 0.3) 100%)',
              border: '1px solid rgba(99, 102, 241, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '0.875rem',
              flexShrink: 0
            }}>
              {user?.full_name?.charAt(0) || 'A'}
            </div>
            <div style={{ minWidth: 0 }}>
              <p style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#ffffff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user?.full_name || 'System Administrator'}
              </p>
              <span className="badge badge-info" style={{ fontSize: '0.625rem', padding: '0.1rem 0.45rem', marginTop: '0.1rem' }}>
                {user?.role || 'ADMIN'}
              </span>
            </div>
          </div>
        </div>

        <button
          onClick={logout}
          className="btn-secondary"
          style={{ width: '100%', justifyContent: 'center', fontSize: '0.8125rem', padding: '0.5rem' }}
        >
          <LogOut style={{ width: '15px', height: '15px', color: '#fb7185' }} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
