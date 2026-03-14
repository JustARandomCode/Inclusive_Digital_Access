import React, { useState, useEffect } from 'react';
import VoiceRecorder from './components/VoiceRecorder';
import FormDisplay from './components/FormDisplay';
import MockDashboard from './components/MockDashboard';
import { authAPI, healthAPI } from './services/api';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [currentForm, setCurrentForm] = useState(null);
  const [activeTab, setActiveTab] = useState('voice');
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mode, setMode] = useState('login'); // 'login' | 'register'

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) verifyAuth();
  }, []);

  // Health check only runs when authenticated — internal service status
  // should not be visible to unauthenticated users
  useEffect(() => {
    if (isAuthenticated) checkHealth();
  }, [isAuthenticated]);

  const verifyAuth = async () => {
    try {
      await authAPI.verify();
      setIsAuthenticated(true);
    } catch {
      localStorage.removeItem('token');
      setIsAuthenticated(false);
    }
  };

  const checkHealth = async () => {
    try {
      const response = await healthAPI.check();
      setHealthStatus(response.data);
    } catch {
      // Health check failure is non-fatal
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await authAPI.login(username, password);
      localStorage.setItem('token', response.data.access_token);
      setIsAuthenticated(true);
      setUsername('');
      setPassword('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await authAPI.register(username, password);
      // Auto-login after registration
      const response = await authAPI.login(username, password);
      localStorage.setItem('token', response.data.access_token);
      setIsAuthenticated(true);
      setUsername('');
      setPassword('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    setCurrentForm(null);
    setHealthStatus(null);
  };

  const handleFormCreated = (form) => {
    setCurrentForm(form);
    setActiveTab('form');
  };

  if (!isAuthenticated) {
    return (
      <div className="login-container">
        <div className="login-box">
          <h1>Inclusive Digital Assistant</h1>
          <p className="subtitle">Voice-Driven Digital Independence</p>

          <div className="mode-toggle">
            <button
              className={mode === 'login' ? 'active' : ''}
              onClick={() => { setMode('login'); setError(''); }}
            >Login</button>
            <button
              className={mode === 'register' ? 'active' : ''}
              onClick={() => { setMode('register'); setError(''); }}
            >Register</button>
          </div>

          <form onSubmit={mode === 'login' ? handleLogin : handleRegister}>
            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                placeholder="Enter username"
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                placeholder={mode === 'register' ? 'Minimum 8 characters' : 'Enter password'}
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? (mode === 'login' ? 'Logging in...' : 'Registering...') : (mode === 'login' ? 'Login' : 'Create Account')}
            </button>
          </form>
          {/* No default password hint here */}
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Inclusive Digital Assistant</h1>
        <button onClick={handleLogout} className="btn-secondary">Logout</button>
      </header>

      <nav className="app-nav">
        <button className={activeTab === 'voice' ? 'active' : ''} onClick={() => setActiveTab('voice')}>
          Voice Input
        </button>
        <button className={activeTab === 'form' ? 'active' : ''} onClick={() => setActiveTab('form')}>
          Form View
        </button>
        <button className={activeTab === 'services' ? 'active' : ''} onClick={() => setActiveTab('services')}>
          Mock Services
        </button>
      </nav>

      <main className="app-main">
        {activeTab === 'voice' && <VoiceRecorder onFormCreated={handleFormCreated} />}
        {activeTab === 'form' && <FormDisplay form={currentForm} />}
        {activeTab === 'services' && <MockDashboard />}
      </main>

      <footer className="app-footer">
        <p>Supporting English, Hindi, and Marathi</p>
        {healthStatus && (
          <div className="footer-health">
            MongoDB: {healthStatus.services?.mongodb} |
            Ollama: {healthStatus.services?.ollama} |
            STT: {healthStatus.services?.stt}
          </div>
        )}
      </footer>
    </div>
  );
}

export default App;
