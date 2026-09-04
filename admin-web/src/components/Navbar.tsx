import React, { useState, useEffect } from 'react';
import { Bell, ShieldCheck, Activity, Search, Sparkles } from 'lucide-react';

interface NavbarProps {
  title: string;
}

export const Navbar: React.FC<NavbarProps> = ({ title }) => {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="navbar">
      {/* Title & Path */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em' }}>
          {title}
        </h1>
        <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem', borderRadius: '0.5rem', background: 'rgba(99, 102, 241, 0.1)', color: '#818cf8', fontWeight: 600, border: '1px solid rgba(99, 102, 241, 0.2)' }}>
          ADMIN PORTAL
        </span>
      </div>

      {/* Action Controls & Live Clock */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {/* Realtime Clock Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.375rem 0.875rem',
          borderRadius: '0.75rem',
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid var(--border-card)',
          fontSize: '0.8125rem',
          fontWeight: 600,
          color: '#cbd5e1',
          fontFamily: "'JetBrains Mono', monospace"
        }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 10px #10b981' }} />
          <span>{time || '00:00:00'}</span>
        </div>

        {/* Biometric Engine Pill */}
        <div className="badge badge-success" style={{ padding: '0.4rem 0.875rem' }}>
          <Activity style={{ width: '13px', height: '13px' }} />
          <span>InsightFace Engine Online</span>
        </div>

        {/* REST API Status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.375rem 0.75rem',
          borderRadius: '0.75rem',
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid var(--border-card)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)'
        }}>
          <ShieldCheck style={{ width: '15px', height: '15px', color: '#818cf8' }} />
          <span>Flask API v1</span>
        </div>

        {/* Notifications Icon */}
        <button
          style={{
            position: 'relative',
            width: '38px',
            height: '38px',
            borderRadius: '0.75rem',
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid var(--border-card)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
          title="System Notifications"
        >
          <Bell style={{ width: '17px', height: '17px' }} />
          <span style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            width: '7px',
            height: '7px',
            borderRadius: '50%',
            background: '#ec4899',
            boxShadow: '0 0 8px #ec4899'
          }} />
        </button>
      </div>
    </header>
  );
};
