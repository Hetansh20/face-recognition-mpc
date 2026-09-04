import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { ShieldAlert, Terminal, RefreshCw, Filter, CheckCircle2, Lock, User, Globe } from 'lucide-react';

export const AuditLogsPage: React.FC = () => {
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [systemLogs, setSystemLogs] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'audit' | 'system'>('audit');
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const [auditRes, sysRes]: any = await Promise.all([
        api.get('/logs/audit'),
        api.get('/logs/system')
      ]);
      if (auditRes.success) setAuditLogs(auditRes.data);
      if (sysRes.success) setSystemLogs(sysRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const getActionBadge = (action: string) => {
    if (action.includes('LOGIN')) return 'badge-success';
    if (action.includes('LOGOUT')) return 'badge-warning';
    if (action.includes('DELETE')) return 'badge-danger';
    return 'badge-info';
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
            <span className="badge badge-warning">Security Monitoring</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Audit Trail Log ID: #SEC-96</span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#ffffff' }}>
            Audit & System Diagnostic Logs
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Immutable security audit trails, administrative authentication logs, and API correlation IDs.
          </p>
        </div>

        <button onClick={fetchLogs} className="btn-secondary">
          <RefreshCw style={{ width: '16px', height: '16px', animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          <span>Refresh Audit Logs</span>
        </button>
      </div>

      {/* Tabs Toolbar */}
      <div className="glass-card" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <button
          onClick={() => setActiveTab('audit')}
          className={activeTab === 'audit' ? 'btn-primary' : 'btn-ghost'}
          style={{ padding: '0.5rem 1rem', fontSize: '0.8125rem' }}
        >
          <ShieldAlert style={{ width: '16px', height: '16px' }} />
          <span>Security Audit Trail ({auditLogs.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('system')}
          className={activeTab === 'system' ? 'btn-primary' : 'btn-ghost'}
          style={{ padding: '0.5rem 1rem', fontSize: '0.8125rem' }}
        >
          <Terminal style={{ width: '16px', height: '16px' }} />
          <span>System Tracing Logs ({systemLogs.length})</span>
        </button>
      </div>

      {/* Logs Table */}
      <div className="table-container">
        {activeTab === 'audit' ? (
          <table className="custom-table">
            <thead>
              <tr>
                <th>Log ID</th>
                <th>Security Action</th>
                <th>User Account Email</th>
                <th>Role</th>
                <th>Client IP Address</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{ width: '28px', height: '28px', border: '3px solid rgba(245, 158, 11, 0.3)', borderTopColor: '#f59e0b', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                      <span>Loading security audit trail...</span>
                    </div>
                  </td>
                </tr>
              ) : auditLogs.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    No security audit logs recorded.
                  </td>
                </tr>
              ) : (
                auditLogs.map((log) => (
                  <tr key={log.id}>
                    <td>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        #{log.id}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${getActionBadge(log.action)}`}>
                        {log.action}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600, color: '#ffffff' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <User style={{ width: '14px', height: '14px', color: '#818cf8' }} />
                        <span>{log.user_email || 'System/Guest'}</span>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>
                        {log.role || 'GUEST'}
                      </span>
                    </td>
                    <td>
                      <span style={{
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: '0.75rem',
                        color: 'var(--text-muted)',
                        background: 'rgba(30, 41, 59, 0.6)',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '0.375rem',
                        border: '1px solid var(--border-card)'
                      }}>
                        {log.ip_address}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        {new Date(log.timestamp).toLocaleString()}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        ) : (
          <table className="custom-table">
            <thead>
              <tr>
                <th>Level</th>
                <th>Correlation Request ID</th>
                <th>Module</th>
                <th>Diagnostic Message</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    Loading system diagnostic logs...
                  </td>
                </tr>
              ) : systemLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                    No system diagnostic logs recorded.
                  </td>
                </tr>
              ) : (
                systemLogs.map((log) => (
                  <tr key={log.id}>
                    <td>
                      <span className="badge badge-success">
                        {log.level}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.75rem', color: '#818cf8' }}>
                        {log.request_id || 'req-system'}
                      </span>
                    </td>
                    <td>
                      <span className="badge badge-cyan" style={{ fontSize: '0.65rem' }}>
                        {log.module}
                      </span>
                    </td>
                    <td style={{ color: '#ffffff', fontFamily: "'JetBrains Mono', monospace", fontSize: '0.8125rem' }}>
                      {log.message}
                    </td>
                    <td>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        {new Date(log.timestamp).toLocaleString()}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
