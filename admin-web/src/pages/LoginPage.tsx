import React, { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Camera, Lock, Mail, ArrowRight, ShieldCheck, Cpu } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('admin123@gmail.com');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.message || err.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };


  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Dynamic Background Glowing Spheres */}
      <div style={{
        position: 'absolute',
        top: '15%',
        left: '20%',
        width: '350px',
        height: '350px',
        background: 'radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, rgba(0,0,0,0) 70%)',
        borderRadius: '50%',
        filter: 'blur(50px)',
        pointerEvents: 'none'
      }} />
      <div style={{
        position: 'absolute',
        bottom: '15%',
        right: '20%',
        width: '400px',
        height: '400px',
        background: 'radial-gradient(circle, rgba(168, 85, 247, 0.2) 0%, rgba(0,0,0,0) 70%)',
        borderRadius: '50%',
        filter: 'blur(60px)',
        pointerEvents: 'none'
      }} />

      {/* Main Glassmorphic Card */}
      <div className="glass-card" style={{
        width: '100%',
        maxWidth: '440px',
        padding: '2.5rem',
        position: 'relative',
        zIndex: 10
      }}>
        {/* Header Icon */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          marginBottom: '1.5rem'
        }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '1.25rem',
            background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%)',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 30px rgba(99, 102, 241, 0.3)'
          }}>
            <Camera style={{ width: '32px', height: '32px', color: '#a5b4fc' }} />
          </div>
        </div>

        {/* Title */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.5rem' }}>
            FaceAttend <span className="gradient-title">Admin</span>
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Biometric Intelligence & Attendance Platform
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div style={{
            padding: '0.875rem 1rem',
            borderRadius: '0.75rem',
            background: 'rgba(244, 63, 94, 0.15)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#fb7185',
            fontSize: '0.84rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <ShieldCheck style={{ width: '18px', height: '18px', flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="input-group">
            <label className="input-label">Administrative Email</label>
            <div className="input-wrapper">
              <Mail className="input-icon" />
              <input
                type="email"
                required
                className="custom-input"
                placeholder="admin@institution.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>

          <div className="input-group">
            <label className="input-label">Passcode / Password</label>
            <div className="input-wrapper">
              <Lock className="input-icon" />
              <input
                type="password"
                required
                className="custom-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{ width: '100%', marginTop: '0.5rem' }}
          >
            {loading ? (
              <span>Authenticating...</span>
            ) : (
              <>
                <span>Sign In to Dashboard</span>
                <ArrowRight style={{ width: '18px', height: '18px' }} />
              </>
            )}
          </button>
        </form>

        {/* Demo Credentials Quick-Fill Section */}
        <div style={{
          marginTop: '1.5rem',
          padding: '1rem',
          borderRadius: '0.875rem',
          background: 'rgba(10, 15, 30, 0.6)',
          border: '1px solid rgba(99, 102, 241, 0.2)'
        }}>
          <p style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: '#818cf8',
            marginBottom: '0.75rem',
            textAlign: 'center'
          }}>
            Instant Demo Sign-In
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <button
              type="button"
              disabled={loading}
              onClick={async () => {
                setEmail('admin123@gmail.com');
                setPassword('admin123');
                setLoading(true);
                setError('');
                try {
                  await login('admin123@gmail.com', 'admin123');
                  navigate('/');
                } catch (err: any) {
                  setError(err.response?.data?.message || err.message || 'Login failed');
                } finally {
                  setLoading(false);
                }
              }}
              className="btn-secondary"
              style={{ justifyContent: 'center', fontSize: '0.75rem', padding: '0.5rem' }}
            >
              🔑 Admin Demo
            </button>
            <button
              type="button"
              disabled={loading}
              onClick={async () => {
                setEmail('hetanshshah2111@gmail.com');
                setPassword('123');
                setLoading(true);
                setError('');
                try {
                  await login('hetanshshah2111@gmail.com', '123');
                  navigate('/');
                } catch (err: any) {
                  setError(err.response?.data?.message || err.message || 'Login failed');
                } finally {
                  setLoading(false);
                }
              }}
              className="btn-secondary"
              style={{ justifyContent: 'center', fontSize: '0.75rem', padding: '0.5rem' }}
            >
              🎓 Faculty Demo
            </button>
          </div>
        </div>

        {/* Footer info */}
        <div style={{
          marginTop: '2rem',
          paddingTop: '1.25rem',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          textAlign: 'center',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem',
          fontSize: '0.75rem',
          color: 'var(--text-dim)'
        }}>
          <Cpu style={{ width: '14px', height: '14px', color: '#6366f1' }} />
          <span>FaceAttend v1.0 • REST API & PostgreSQL Protected</span>
        </div>
      </div>
    </div>
  );
};
