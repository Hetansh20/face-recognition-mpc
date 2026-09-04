import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Plus, Search, Trash2, Camera, CheckCircle2, AlertCircle, Upload, X, Filter, Sparkles, UserCheck } from 'lucide-react';

export const StudentsPage: React.FC = () => {
  const [students, setStudents] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showFaceModal, setShowFaceModal] = useState<number | null>(null);

  const [formData, setFormData] = useState({
    gr_number: '',
    enrollment_number: '',
    name: '',
    email: '',
    department: 'ICT',
    roll_number: '',
    phone: '',
  });

  const [faceFile, setFaceFile] = useState<File | null>(null);
  const [uploadingFace, setUploadingFace] = useState(false);

  const fetchStudents = async () => {
    setLoading(true);
    try {
      const res: any = await api.get(`/students${search ? `?search=${search}` : ''}`);
      if (res.success) setStudents(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [search]);

  const filteredStudents = students.filter(s => {
    if (departmentFilter === 'ALL') return true;
    if (departmentFilter === 'ENROLLED') return s.has_face_registered;
    if (departmentFilter === 'PENDING') return !s.has_face_registered;
    return s.department === departmentFilter;
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res: any = await api.post('/students', formData);
      if (res.success) {
        setShowAddModal(false);
        setFormData({ gr_number: '', enrollment_number: '', name: '', email: '', department: 'ICT', roll_number: '', phone: '' });
        fetchStudents();
      }
    } catch (err: any) {
      alert(err.error?.message || 'Error creating student');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to deactivate this student record?')) return;
    try {
      await api.delete(`/students/${id}`);
      fetchStudents();
    } catch (e) {
      alert('Failed to delete student');
    }
  };

  const handleFaceUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showFaceModal || !faceFile) return;
    setUploadingFace(true);

    const fd = new FormData();
    fd.append('image', faceFile);

    try {
      const res: any = await api.post(`/students/${showFaceModal}/face-registration`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (res.success) {
        alert('Face profile registered successfully!');
        setShowFaceModal(null);
        setFaceFile(null);
        fetchStudents();
      }
    } catch (err: any) {
      alert(err.error?.message || 'Face registration failed');
    } finally {
      setUploadingFace(false);
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
            <span className="badge badge-info">Student Management</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Total Records: {students.length}</span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#ffffff' }}>
            Student Directory
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Manage student registrations, enrollment status, and InsightFace 512-d embeddings.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary"
        >
          <Plus style={{ width: '18px', height: '18px' }} />
          <span>Register New Student</span>
        </button>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="glass-card" style={{ padding: '1rem 1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div className="input-wrapper" style={{ flex: 1, minWidth: '280px' }}>
          <Search className="input-icon" style={{ width: '18px', height: '18px' }} />
          <input
            type="text"
            placeholder="Search by GR Number, Student Name, Email, Class..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="custom-input"
          />
        </div>

        {/* Filter Chips */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          {['ALL', 'ENROLLED', 'PENDING', 'ICT'].map((filter) => (
            <button
              key={filter}
              onClick={() => setDepartmentFilter(filter)}
              className={departmentFilter === filter ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '0.4rem 0.875rem', fontSize: '0.75rem', borderRadius: '0.625rem' }}
            >
              {filter === 'ALL' ? 'All Students' : filter === 'ENROLLED' ? 'Biometric Enrolled' : filter === 'PENDING' ? 'Pending Photos' : filter}
            </button>
          ))}
        </div>
      </div>

      {/* Students Table */}
      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th>GR / ID</th>
              <th>Student Name</th>
              <th>Email Address</th>
              <th>Class / Dept</th>
              <th>Face Biometrics</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '28px', height: '28px', border: '3px solid rgba(99, 102, 241, 0.3)', borderTopColor: '#6366f1', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                    <span>Loading student records...</span>
                  </div>
                </td>
              </tr>
            ) : filteredStudents.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  No student records match your query.
                </td>
              </tr>
            ) : (
              filteredStudents.map((stu) => (
                <tr key={stu.id}>
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
                      {stu.gr_number || `STU-${stu.id}`}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{
                        width: '34px',
                        height: '34px',
                        borderRadius: '50%',
                        background: 'rgba(168, 85, 247, 0.15)',
                        border: '1px solid rgba(168, 85, 247, 0.3)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#c084fc',
                        fontWeight: 700,
                        fontSize: '0.8125rem'
                      }}>
                        {stu.name?.charAt(0) || 'S'}
                      </div>
                      <div>
                        <p style={{ fontWeight: 600, color: '#ffffff' }}>{stu.name}</p>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Roll #{stu.roll_number || 'N/A'}</p>
                      </div>
                    </div>
                  </td>
                  <td style={{ color: 'var(--text-muted)' }}>{stu.email}</td>
                  <td>
                    <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                      {stu.class_name || stu.department || 'ICT'}
                    </span>
                  </td>
                  <td>
                    {stu.has_face_registered ? (
                      <span className="badge badge-success">
                        <CheckCircle2 style={{ width: '13px', height: '13px' }} /> Enrolled (512-d)
                      </span>
                    ) : (
                      <button
                        onClick={() => setShowFaceModal(stu.id)}
                        className="badge badge-warning"
                        style={{ cursor: 'pointer', border: '1px dashed rgba(245, 158, 11, 0.5)' }}
                      >
                        <Camera style={{ width: '13px', height: '13px' }} /> Upload Photo
                      </button>
                    )}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      onClick={() => handleDelete(stu.id)}
                      className="btn-secondary"
                      style={{ padding: '0.4rem 0.6rem', color: '#fb7185', borderColor: 'rgba(244, 63, 94, 0.3)' }}
                      title="Deactivate Student"
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

      {/* Add Student Modal */}
      {showAddModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(7, 9, 19, 0.85)', backdropFilter: 'blur(12px)', zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div className="glass-card" style={{ width: '100%', maxWidth: '520px', padding: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-card)' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff' }}>Register New Student</h3>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Add profile to database</p>
              </div>
              <button onClick={() => setShowAddModal(false)} className="btn-ghost" style={{ padding: '0.4rem' }}>
                <X style={{ width: '20px', height: '20px' }} />
              </button>
            </div>

            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="input-group">
                  <label className="input-label">GR Number *</label>
                  <input type="text" required value={formData.gr_number} onChange={e=>setFormData({...formData, gr_number: e.target.value})} className="custom-input" style={{ paddingLeft: '1rem' }} placeholder="GR-141667" />
                </div>
                <div className="input-group">
                  <label className="input-label">Full Name *</label>
                  <input type="text" required value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} className="custom-input" style={{ paddingLeft: '1rem' }} placeholder="John Doe" />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label">Email Address *</label>
                <input type="email" required value={formData.email} onChange={e=>setFormData({...formData, email: e.target.value})} className="custom-input" style={{ paddingLeft: '1rem' }} placeholder="student@university.edu" />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="input-group">
                  <label className="input-label">Department</label>
                  <input type="text" value={formData.department} onChange={e=>setFormData({...formData, department: e.target.value})} className="custom-input" style={{ paddingLeft: '1rem' }} />
                </div>
                <div className="input-group">
                  <label className="input-label">Roll Number</label>
                  <input type="text" value={formData.roll_number} onChange={e=>setFormData({...formData, roll_number: e.target.value})} className="custom-input" style={{ paddingLeft: '1rem' }} placeholder="92500133053" />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-card)' }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-primary">Save Student</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload Face Photo Modal */}
      {showFaceModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(7, 9, 19, 0.85)', backdropFilter: 'blur(12px)', zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div className="glass-card" style={{ width: '100%', maxWidth: '460px', padding: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-card)' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff' }}>Face Profile Biometrics</h3>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>InsightFace 512-d Embedding Extractor</p>
              </div>
              <button onClick={() => setShowFaceModal(null)} className="btn-ghost" style={{ padding: '0.4rem' }}>
                <X style={{ width: '20px', height: '20px' }} />
              </button>
            </div>

            <form onSubmit={handleFaceUpload} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{
                border: '2px dashed rgba(99, 102, 241, 0.4)',
                borderRadius: '1rem',
                padding: '2rem 1.5rem',
                textAlign: 'center',
                background: 'rgba(10, 15, 30, 0.5)'
              }}>
                <Upload style={{ width: '36px', height: '36px', color: '#818cf8', margin: '0 auto 0.75rem' }} />
                <p style={{ fontSize: '0.9375rem', fontWeight: 600, color: '#ffffff' }}>Upload High Resolution Photo</p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>PNG, JPG or WEBP with clear front-facing lighting</p>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setFaceFile(e.target.files?.[0] || null)}
                  style={{ marginTop: '1rem', fontSize: '0.8125rem', color: 'var(--text-muted)' }}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', paddingTop: '1rem', borderTop: '1px solid var(--border-card)' }}>
                <button type="button" onClick={() => setShowFaceModal(null)} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={uploadingFace} className="btn-primary">
                  {uploadingFace ? 'Extracting Embeddings...' : 'Train Biometrics'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
