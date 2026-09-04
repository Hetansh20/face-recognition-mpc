import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { UserCheck, Plus, Search, Trash2, Key, X, Mail, Building } from 'lucide-react';

export const FacultyPage: React.FC = () => {
  const [faculty, setFaculty] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    department: 'Computer Science',
    passcode: '123456',
  });

  const fetchFaculty = async () => {
    setLoading(true);
    try {
      const res: any = await api.get(`/faculty${search ? `?search=${search}` : ''}`);
      if (res.success) setFaculty(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFaculty();
  }, [search]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res: any = await api.post('/faculty', formData);
      if (res.success) {
        setShowAddModal(false);
        setFormData({ name: '', email: '', department: 'Computer Science', passcode: '123456' });
        fetchFaculty();
      }
    } catch (err: any) {
      alert(err.error?.message || 'Failed to create faculty member');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Deactivate this faculty account?')) return;
    try {
      await api.delete(`/faculty/${id}`);
      fetchFaculty();
    } catch (e) {
      alert('Failed to deactivate faculty member');
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
            <span className="badge badge-info">Faculty Management</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Authorized Presenters: {faculty.length}</span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#ffffff' }}>
            Faculty Directory
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Faculty accounts, department assignments, and authentication passcode credentials.
          </p>
        </div>

        <button onClick={() => setShowAddModal(true)} className="btn-primary">
          <Plus style={{ width: '18px', height: '18px' }} />
          <span>Add Faculty Member</span>
        </button>
      </div>

      {/* Search Input Bar */}
      <div className="glass-card" style={{ padding: '1rem 1.25rem' }}>
        <div className="input-wrapper">
          <Search className="input-icon" style={{ width: '18px', height: '18px' }} />
          <input
            type="text"
            placeholder="Search by faculty member name, email address, or department..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="custom-input"
          />
        </div>
      </div>

      {/* Faculty Table */}
      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Faculty Name</th>
              <th>Email Address</th>
              <th>Department</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '28px', height: '28px', border: '3px solid rgba(168, 85, 247, 0.3)', borderTopColor: '#a855f7', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                    <span>Loading faculty records...</span>
                  </div>
                </td>
              </tr>
            ) : faculty.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  No faculty records found matching your query.
                </td>
              </tr>
            ) : (
              faculty.map((fac) => (
                <tr key={fac.id}>
                  <td>
                    <span style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontWeight: 600,
                      color: '#c084fc',
                      background: 'rgba(168, 85, 247, 0.1)',
                      padding: '0.25rem 0.6rem',
                      borderRadius: '0.5rem',
                      fontSize: '0.8125rem',
                      border: '1px solid rgba(168, 85, 247, 0.2)'
                    }}>
                      FAC-{fac.id}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.3) 0%, rgba(99, 102, 241, 0.3) 100%)',
                        border: '1px solid rgba(168, 85, 247, 0.4)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#ffffff',
                        fontWeight: 700,
                        fontSize: '0.875rem'
                      }}>
                        {fac.name?.charAt(0) || 'F'}
                      </div>
                      <div>
                        <p style={{ fontWeight: 600, color: '#ffffff' }}>{fac.name}</p>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Faculty Presenter</p>
                      </div>
                    </div>
                  </td>
                  <td style={{ color: 'var(--text-muted)' }}>{fac.email}</td>
                  <td>
                    <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                      {fac.department || 'Computer Science'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      onClick={() => handleDelete(fac.id)}
                      className="btn-secondary"
                      style={{ padding: '0.4rem 0.6rem', color: '#fb7185', borderColor: 'rgba(244, 63, 94, 0.3)' }}
                      title="Deactivate Faculty Member"
                    >
                      <Trash2 style={{ width: '15px', height: '15px' }} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Add Faculty Modal */}
      {showAddModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(7, 9, 19, 0.85)', backdropFilter: 'blur(12px)', zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div className="glass-card" style={{ width: '100%', maxWidth: '480px', padding: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-card)' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff' }}>Add Faculty Member</h3>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Create presenter login account</p>
              </div>
              <button onClick={() => setShowAddModal(false)} className="btn-ghost" style={{ padding: '0.4rem' }}>
                <X style={{ width: '20px', height: '20px' }} />
              </button>
            </div>

            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="input-group">
                <label className="input-label">Faculty Full Name *</label>
                <input type="text" required value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} className="custom-input" style={{ paddingLeft: '1rem' }} placeholder="Prof. Jane Smith" />
              </div>

              <div className="input-group">
                <label className="input-label">Email Address *</label>
                <input type="email" required value={formData.email} onChange={e=>setFormData({...formData, email: e.target.value})} className="custom-input" style={{ paddingLeft: '1rem' }} placeholder="faculty@university.edu" />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="input-group">
                  <label className="input-label">Department</label>
                  <input type="text" value={formData.department} onChange={e=>setFormData({...formData, department: e.target.value})} className="custom-input" style={{ paddingLeft: '1rem' }} />
                </div>
                <div className="input-group">
                  <label className="input-label">Passcode *</label>
                  <input type="text" required value={formData.passcode} onChange={e=>setFormData({...formData, passcode: e.target.value})} className="custom-input" style={{ paddingLeft: '1rem' }} placeholder="123456" />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-card)' }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-primary">Save Faculty Member</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
