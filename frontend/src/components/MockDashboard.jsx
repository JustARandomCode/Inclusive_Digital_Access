import React, { useState } from 'react';
import { formsAPI } from '../services/api';
import './MockDashboard.css';;

function MockDashboard() {
  const [selectedService, setSelectedService] = useState('bank');
  const [selectedAction, setSelectedAction] = useState('kyc');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const services = {
    bank: {
      name: 'Banking Services',
      icon: '🏦',
      actions: [
        { id: 'kyc', label: 'KYC Verification', data: { name: 'Test User', dob: '1960-01-01' } },
        { id: 'account', label: 'Account Details', data: { account_number: '1234567890' } },
      ],
    },
    health: {
      name: 'Healthcare Services',
      icon: '🏥',
      actions: [
        { id: 'appointment', label: 'Book Appointment', data: { patient: 'Test User', date: '2024-12-28' } },
        { id: 'records', label: 'View Medical Records', data: { patient_id: 'P12345' } },
      ],
    },
    government: {
      name: 'Government Services',
      icon: '🏛️',
      actions: [
        { id: 'form', label: 'Submit Form', data: { form_type: 'pension', applicant: 'Test User' } },
        { id: 'status', label: 'Check Status', data: { application_id: 'APP12345' } },
      ],
    },
  };

  const handleServiceCall = async () => {
    setLoading(true);
    setError('');
    setResponse(null);

    try {
      const action = services[selectedService].actions.find(a => a.id === selectedAction);
      const result = await formsAPI.mockService(selectedService, selectedAction, action.data);
      setResponse(result.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Service call failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mock-dashboard">
      <h2>Mock Service Integration</h2>
      <p className="dashboard-subtitle">
        Simulate interactions with banking, healthcare, and government services
      </p>

      <div className="service-grid">
        {Object.entries(services).map(([key, service]) => (
          <div
            key={key}
            className={`service-card ${selectedService === key ? 'active' : ''}`}
            onClick={() => {
              setSelectedService(key);
              setSelectedAction(service.actions[0].id);
              setResponse(null);
            }}
          >
            <div className="service-icon">{service.icon}</div>
            <div className="service-name">{service.name}</div>
          </div>
        ))}
      </div>

      <div className="action-section">
        <h3>Available Actions</h3>
        <div className="action-list">
          {services[selectedService].actions.map((action) => (
            <button
              key={action.id}
              className={`action-button ${selectedAction === action.id ? 'active' : ''}`}
              onClick={() => {
                setSelectedAction(action.id);
                setResponse(null);
              }}
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>

      <div className="request-section">
        <h3>Request Data</h3>
        <pre className="data-display">
          {JSON.stringify(
            services[selectedService].actions.find(a => a.id === selectedAction)?.data,
            null,
            2
          )}
        </pre>

        <button
          onClick={handleServiceCall}
          disabled={loading}
          className="btn-primary call-service-btn"
        >
          {loading ? 'Calling Service...' : '📞 Call Service'}
        </button>
      </div>

      {response && (
        <div className="response-section">
          <h3>Service Response</h3>
          <div className="response-card">
            <div className="response-status success">
              ✓ {response.status.toUpperCase()}
            </div>
            <div className="response-message">{response.message}</div>
            {response.data && (
              <pre className="data-display">
                {JSON.stringify(response.data, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}

export default MockDashboard;