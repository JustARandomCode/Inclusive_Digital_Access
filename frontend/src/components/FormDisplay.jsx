import React, { useState, useEffect } from 'react';
import { formsAPI, voiceAPI } from '../services/api';
import './FormDisplay.css';

function FormDisplay({ form: initialForm }) {
  const [form, setForm] = useState(initialForm);
  const [forms, setForms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    loadForms();
  }, []);

  useEffect(() => {
    setForm(initialForm);
    setEditMode(false);
    setAudioUrl('');
    setError('');
  }, [initialForm]);

  const loadForms = async () => {
    try {
      const response = await formsAPI.list();
      setForms(response.data);
    } catch (err) {
      // Non-fatal — user can still work with the current form
      console.error('Failed to load forms list:', err);
    }
  };

  const handleFieldChange = (fieldName, newValue) => {
    setForm((prev) => ({
      ...prev,
      fields: prev.fields.map((f) =>
        f.field_name === fieldName ? { ...f, field_value: newValue } : f
      ),
    }));
  };

  const handleSaveForm = async () => {
    setLoading(true);
    setError('');
    setSaveSuccess(false);
    try {
      // formsAPI.update strips _id before sending
      await formsAPI.update(form.form_id, form);
      setEditMode(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      await loadForms();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save form');
    } finally {
      setLoading(false);
    }
  };

  const handleReadAloud = async () => {
    if (!form) return;
    setLoading(true);
    setError('');
    try {
      const summary = form.fields
        .filter((f) => f.field_value)
        .map((f) => `${f.field_name.replace(/_/g, ' ')}: ${f.field_value}`)
        .join('. ');

      const response = await voiceAPI.synthesize(summary, 'en');
      setAudioUrl(response.data.audio_url);
    } catch (err) {
      setError(err.response?.data?.detail || 'Text-to-speech failed');
    } finally {
      setLoading(false);
    }
  };

  const selectForm = (selected) => {
    setForm(selected);
    setEditMode(false);
    setAudioUrl('');
    setError('');
  };

  if (!form && forms.length === 0) {
    return (
      <div className="form-display">
        <div className="empty-state">
          <h2>No Forms Available</h2>
          <p>Use the Voice Input tab to create your first form.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="form-display">
      <div className="form-header">
        <h2>Form View</h2>
        {forms.length > 0 && (
          <select
            onChange={(e) => {
              const selected = forms.find((f) => f.form_id === e.target.value);
              if (selected) selectForm(selected);
            }}
            value={form?.form_id || ''}
            className="form-selector"
            aria-label="Select a form"
          >
            <option value="">Select a form...</option>
            {forms.map((f) => (
              <option key={f.form_id} value={f.form_id}>
                {f.form_type} — {new Date(f.created_at).toLocaleDateString()}
              </option>
            ))}
          </select>
        )}
      </div>

      {form && (
        <>
          {form.status === 'extraction_failed' && (
            <div className="warning-message" role="alert">
              Voice extraction partially failed. Please review and correct the fields below before saving.
            </div>
          )}

          {saveSuccess && (
            <div className="success-message" role="status">
              Form saved successfully.
            </div>
          )}

          <div className="form-metadata">
            <div className="metadata-item">
              <strong>Form Type:</strong> {form.form_type}
            </div>
            <div className="metadata-item">
              <strong>Status:</strong>
              <span className={`status-badge ${form.status}`}>{form.status}</span>
            </div>
            <div className="metadata-item">
              <strong>Created:</strong> {new Date(form.created_at).toLocaleString()}
            </div>
          </div>

          <div className="form-fields">
            {form.fields.map((field) => (
              // field_name is unique per form — safe as key
              <div key={field.field_name} className="field-group">
                <label htmlFor={`field-${field.field_name}`}>
                  {field.field_name.replace(/_/g, ' ').toUpperCase()}
                </label>
                {editMode ? (
                  field.field_type === 'textarea' ? (
                    <textarea
                      id={`field-${field.field_name}`}
                      value={field.field_value || ''}
                      onChange={(e) => handleFieldChange(field.field_name, e.target.value)}
                      rows="4"
                    />
                  ) : (
                    <input
                      id={`field-${field.field_name}`}
                      type={field.field_type === 'date' ? 'text' : field.field_type}
                      value={field.field_value || ''}
                      onChange={(e) => handleFieldChange(field.field_name, e.target.value)}
                    />
                  )
                ) : (
                  <div className="field-value">
                    {field.field_value || <span className="empty-field">Not provided</span>}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="form-actions">
            {editMode ? (
              <>
                <button onClick={handleSaveForm} disabled={loading} className="btn-primary">
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  onClick={() => { setEditMode(false); setForm(initialForm || form); }}
                  className="btn-secondary"
                  disabled={loading}
                >
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button onClick={() => setEditMode(true)} className="btn-secondary">
                  ✏️ Edit Form
                </button>
                <button onClick={handleReadAloud} disabled={loading} className="btn-secondary">
                  {loading ? 'Generating...' : '🔊 Read Aloud'}
                </button>
              </>
            )}
          </div>

          {audioUrl && (
            <div className="audio-playback">
              <h4>Audio Summary</h4>
              <audio controls src={audioUrl} autoPlay aria-label="Form audio summary" />
            </div>
          )}

          {error && <div className="error-message" role="alert">{error}</div>}
        </>
      )}
    </div>
  );
}

export default FormDisplay;
