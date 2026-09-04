import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Smartphone, CheckCircle, ShieldOff, RefreshCw, Cpu, Wifi, ShieldAlert, Sparkles } from 'lucide-react';

export const DevicesPage: React.FC = () => {
  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const res: any = await api.get('/devices');
      if (res.success) setDevices(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const toggleStatus = async (deviceId: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'ACTIVE' ? 'BLOCKED' : 'ACTIVE';
    try {
      await api.put(`/devices/${deviceId}/status`, { status: nextStatus });
      fetchDevices();
    } catch (e) {
      alert('Failed to update device status');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Header Banner */}
      <div className="glass-card" style={{
        padding: '1.75rem 2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.375rem' }}>
            <span className="badge badge-cyan">Device Security Control</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Kotlin Android 8.2.2</span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#ffffff' }}>
            Registered Mobile Devices
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Authorized Kotlin Android client app hardware registration and real-time device access control.
          </p>
        </div>

        <button onClick={fetchDevices} className="btn-secondary">
          <RefreshCw style={{ width: '16px', height: '16px', animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          <span>Refresh Registered Devices</span>
        </button>
      </div>

      {/* Devices Overview Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
        <div className="glass-card" style={{ padding: '1.25rem 1.5rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Total Registered Apps</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff', marginTop: '0.25rem' }}>{devices.length || 1}</div>
          <div style={{ fontSize: '0.75rem', color: '#818cf8', marginTop: '0.25rem' }}>FaceAttend Android Client</div>
        </div>

        <div className="glass-card" style={{ padding: '1.25rem 1.5rem' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>Active Stream Feeds</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff', marginTop: '0.25rem' }}>1 Active</div>
          <div style={{ fontSize: '0.75rem', color: '#10b981', marginTop: '0.25rem' }}>CameraX Real-time Pipeline</div>
        </div>
      </div>

      {/* Devices Table */}
      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th>Device ID</th>
              <th>Device Model Name</th>
              <th>OS Platform</th>
              <th>App Version</th>
              <th>Status</th>
              <th>Last Synced</th>
              <th style={{ textAlign: 'right' }}>Access Control</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '28px', height: '28px', border: '3px solid rgba(6, 182, 212, 0.3)', borderTopColor: '#06b6d4', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                    <span>Loading registered mobile devices...</span>
                  </div>
                </td>
              </tr>
            ) : devices.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '3.5rem 2rem', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', maxWidth: '400px', margin: '0 auto' }}>
                    <div style={{
                      width: '60px',
                      height: '60px',
                      borderRadius: '1.25rem',
                      background: 'rgba(99, 102, 241, 0.12)',
                      border: '1px solid rgba(99, 102, 241, 0.25)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#818cf8'
                    }}>
                      <Smartphone style={{ width: '30px', height: '30px' }} />
                    </div>
                    <div>
                      <h4 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#ffffff', marginBottom: '0.25rem' }}>
                        No Registered Mobile Devices
                      </h4>
                      <p style={{ fontSize: '0.8125rem', color: 'var(--text-dim)', lineHeight: 1.5 }}>
                        Launch the FaceAttend Android app on your mobile device to register it automatically with the REST API.
                      </p>
                    </div>
                  </div>
                </td>
              </tr>
            ) : (
              devices.map((dev) => (
                <tr key={dev.id}>
                  <td>
                    <span style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontWeight: 600,
                      color: '#818cf8',
                      background: 'rgba(99, 102, 241, 0.1)',
                      padding: '0.25rem 0.6rem',
                      borderRadius: '0.5rem',
                      fontSize: '0.8125rem',
                      border: '1px solid rgba(99, 102, 241, 0.2)'
                    }}>
                      {dev.device_id}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{
                        width: '34px',
                        height: '34px',
                        borderRadius: '0.75rem',
                        background: 'rgba(6, 182, 212, 0.15)',
                        border: '1px solid rgba(6, 182, 212, 0.3)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#38bdf8'
                      }}>
                        <Smartphone style={{ width: '18px', height: '18px' }} />
                      </div>
                      <span style={{ fontWeight: 600, color: '#ffffff' }}>{dev.device_name || 'Android Device'}</span>
                    </div>
                  </td>
                  <td style={{ color: 'var(--text-muted)' }}>{dev.platform || 'Android 14 (API 34)'}</td>
                  <td>
                    <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                      {dev.app_version || 'v1.0.0'}
                    </span>
                  </td>
                  <td>
                    {dev.status === 'ACTIVE' ? (
                      <span className="badge badge-success">
                        <CheckCircle style={{ width: '13px', height: '13px' }} /> ACTIVE
                      </span>
                    ) : (
                      <span className="badge badge-danger">
                        <ShieldOff style={{ width: '13px', height: '13px' }} /> BLOCKED
                      </span>
                    )}
                  </td>
                  <td>
                    <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {new Date(dev.last_seen).toLocaleString()}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      onClick={() => toggleStatus(dev.device_id, dev.status)}
                      className={dev.status === 'ACTIVE' ? 'btn-secondary' : 'btn-primary'}
                      style={{
                        padding: '0.4rem 0.875rem',
                        fontSize: '0.75rem',
                        color: dev.status === 'ACTIVE' ? '#fb7185' : '#ffffff',
                        borderColor: dev.status === 'ACTIVE' ? 'rgba(244, 63, 94, 0.3)' : undefined
                      }}
                    >
                      {dev.status === 'ACTIVE' ? 'Block Access' : 'Authorize Device'}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
