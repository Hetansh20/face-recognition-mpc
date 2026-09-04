import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Calendar, Plus, Trash2, Clock, MapPin, X, BookOpen, User } from 'lucide-react';

export const TimetablePage: React.FC = () => {
  const [timetables, setTimetables] = useState<any[]>([]);
  const [faculties, setFaculties] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  const [formData, setFormData] = useState({
    faculty_id: '',
    class_name: 'CS-SEM6-A',
    semester: 'Semester 6',
    subject_name: 'Computer Networks',
    day_of_week: 'Monday',
    start_time: '09:00',
    end_time: '10:00',
    room_number: 'Lab 102'
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [ttRes, facRes]: any = await Promise.all([
        api.get('/timetables'),
        api.get('/faculty')
      ]);
      if (ttRes.success) setTimetables(ttRes.data);
      if (facRes.success) setFaculties(facRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.faculty_id) {
      alert('Please select a faculty member');
      return;
    }
    try {
      const res: any = await api.post('/timetables', {
        ...formData,
        faculty_id: parseInt(formData.faculty_id)
      });
      if (res.success) {
        setShowAddModal(false);
        fetchData();
      }
    } catch (err: any) {
      alert(err.error?.message || 'Failed to create timetable');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this timetable entry?')) return;
    try {
      await api.delete(`/timetables/${id}`);
      fetchData();
    } catch (e) {
      alert('Failed to delete timetable entry');
    }
  };

  const getDayBadgeColor = (day: string) => {
    switch (day) {
      case 'Monday': return 'badge-info';
      case 'Tuesday': return 'badge-cyan';
      case 'Wednesday': return 'badge-success';
      case 'Thursday': return 'badge-warning';
      case 'Friday': return 'badge-danger';
      default: return 'badge-info';
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
            <span className="badge badge-cyan">Automated Scheduling</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Slots Configured: {timetables.length}</span>
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#ffffff' }}>
            Timetable & Class Schedules
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Configure weekly course timetables with semester mapping for mobile attendance session resolution.
          </p>
        </div>

        <button onClick={() => setShowAddModal(true)} className="btn-primary">
          <Plus style={{ width: '18px', height: '18px' }} />
          <span>Add Schedule Slot</span>
        </button>
      </div>

      {/* Timetable Table */}
      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th>Day of Week</th>
              <th>Time Interval</th>
              <th>Class / Batch</th>
              <th>Semester</th>
              <th>Subject</th>
              <th>Faculty Presenter</th>
              <th>Room / Lab</th>
              <th style={{ textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: '28px', height: '28px', border: '3px solid rgba(6, 182, 212, 0.3)', borderTopColor: '#06b6d4', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                    <span>Loading schedule timetable...</span>
                  </div>
                </td>
              </tr>
            ) : timetables.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  No timetable entries configured yet.
                </td>
              </tr>
            ) : (
              timetables.map((tt) => (
                <tr key={tt.id}>
                  <td>
                    <span className={`badge ${getDayBadgeColor(tt.day_of_week)}`}>
                      {tt.day_of_week}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontFamily: "'JetBrains Mono', monospace", fontSize: '0.8125rem', color: '#ffffff' }}>
                      <Clock style={{ width: '14px', height: '14px', color: '#818cf8' }} />
                      <span>{tt.start_time} - {tt.end_time}</span>
                    </div>
                  </td>
                  <td>
                    <span className="badge badge-info" style={{ fontWeight: 700 }}>
                      {tt.class_name}
                    </span>
                  </td>
                  <td>
                    <span className="badge badge-purple" style={{ fontWeight: 700 }}>
                      {tt.semester || 'N/A'}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600, color: '#ffffff' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <BookOpen style={{ width: '15px', height: '15px', color: '#c084fc' }} />
                      <span>{tt.subject_name || 'N/A'}</span>
                    </div>
                  </td>
                  <td style={{ color: 'var(--text-muted)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <User style={{ width: '14px', height: '14px', color: '#94a3b8' }} />
                      <span>{tt.faculty_name}</span>
                    </div>
                  </td>
                  <td>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      padding: '0.25rem 0.6rem',
                      borderRadius: '0.5rem',
                      background: 'rgba(30, 41, 59, 0.8)',
                      border: '1px solid var(--border-card)',
                      fontSize: '0.75rem',
                      color: 'var(--text-main)',
                      fontWeight: 600
                    }}>
                      <MapPin style={{ width: '13px', height: '13px', color: '#f43f5e' }} />
                      {tt.room_number || 'Room N/A'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      onClick={() => handleDelete(tt.id)}
                      className="btn-secondary"
                      style={{ padding: '0.4rem 0.6rem', color: '#fb7185', borderColor: 'rgba(244, 63, 94, 0.3)' }}
                      title="Delete Schedule Entry"
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

      {/* Add Schedule Modal */}
      {showAddModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(7, 9, 19, 0.85)', backdropFilter: 'blur(12px)', zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
          <div className="glass-card" style={{ width: '100%', maxWidth: '540px', padding: '2rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-card)' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff' }}>Schedule Timetable Slot</h3>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Configure automated class window & semester</p>
              </div>
              <button onClick={() => setShowAddModal(false)} className="btn-ghost" style={{ padding: '0.4rem' }}>
                <X style={{ width: '20px', height: '20px' }} />
              </button>
            </div>

            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="input-group">
                <label className="input-label">Faculty Member *</label>
                <select
                  value={formData.faculty_id}
                  onChange={(e) => setFormData({ ...formData, faculty_id: e.target.value })}
                  className="custom-input"
                  style={{ paddingLeft: '1rem' }}
                  required
                >
                  <option value="">-- Select Faculty --</option>
                  {faculties.map((f) => (
                    <option key={f.id} value={f.id}>{f.name} ({f.department})</option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
                <div className="input-group">
                  <label className="input-label">Class / Batch *</label>
                  <input type="text" required value={formData.class_name} onChange={e=>setFormData({...formData, class_name: e.target.value})} className="custom-input" style={{ paddingLeft: '0.75rem' }} placeholder="6EK1" />
                </div>
                <div className="input-group">
                  <label className="input-label">Semester *</label>
                  <select
                    value={formData.semester}
                    onChange={(e) => setFormData({ ...formData, semester: e.target.value })}
                    className="custom-input"
                    style={{ paddingLeft: '0.5rem', paddingRight: '0.5rem' }}
                    required
                  >
                    <option value="Semester 1">Semester 1</option>
                    <option value="Semester 2">Semester 2</option>
                    <option value="Semester 3">Semester 3</option>
                    <option value="Semester 4">Semester 4</option>
                    <option value="Semester 5">Semester 5</option>
                    <option value="Semester 6">Semester 6</option>
                    <option value="Semester 7">Semester 7</option>
                    <option value="Semester 8">Semester 8</option>
                  </select>
                </div>
                <div className="input-group">
                  <label className="input-label">Subject Name</label>
                  <input type="text" value={formData.subject_name} onChange={e=>setFormData({...formData, subject_name: e.target.value})} className="custom-input" style={{ paddingLeft: '0.75rem' }} placeholder="MIS" />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
                <div className="input-group">
                  <label className="input-label">Day *</label>
                  <select value={formData.day_of_week} onChange={e=>setFormData({...formData, day_of_week: e.target.value})} className="custom-input" style={{ paddingLeft: '0.5rem', paddingRight: '0.5rem' }}>
                    {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>
                <div className="input-group">
                  <label className="input-label">Start Time</label>
                  <input type="text" required value={formData.start_time} onChange={e=>setFormData({...formData, start_time: e.target.value})} className="custom-input" style={{ paddingLeft: '0.75rem' }} placeholder="09:00" />
                </div>
                <div className="input-group">
                  <label className="input-label">End Time</label>
                  <input type="text" required value={formData.end_time} onChange={e=>setFormData({...formData, end_time: e.target.value})} className="custom-input" style={{ paddingLeft: '0.75rem' }} placeholder="10:00" />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label">Room / Lab Number</label>
                <input type="text" value={formData.room_number} onChange={e=>setFormData({...formData, room_number: e.target.value})} className="custom-input" style={{ paddingLeft: '1rem' }} placeholder="Lab 102" />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-card)' }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-primary">Save Schedule</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
