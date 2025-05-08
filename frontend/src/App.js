import React, { useState } from 'react';
import './App.css';

function App() {
  // Authentication state
  const [loggedIn, setLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [showSignup, setShowSignup] = useState(false);
  const [signupData, setSignupData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: ''
  });
  const [signupError, setSignupError] = useState('');
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);

  // Uploader state
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [cleanedData, setCleanedData] = useState(null);
  const [errors, setErrors] = useState(null);
  const [message, setMessage] = useState('');

  // Handle login
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    try {
      const response = await fetch('http://localhost:8000/login/', {
        method: 'POST',
        headers: {
          'Authorization': 'Basic ' + btoa(username + ':' + password)
        }
      });
      if (response.ok) {
        setLoggedIn(true);
      } else {
        setLoginError('Invalid credentials.');
      }
    } catch (err) {
      setLoginError('Login failed.');
    }
  };

  // Handle signup
  const handleSignup = async (e) => {
    e.preventDefault();
    setSignupError('');

    // Validate passwords match
    if (signupData.password !== signupData.confirmPassword) {
      setSignupError('Passwords do not match');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/signup/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: signupData.email,
          password: signupData.password,
          full_name: signupData.fullName
        }),
      });

      if (response.ok) {
        // Switch back to login view after successful signup
        setShowSignup(false);
        setUsername(signupData.email);
        setSignupData({
          email: '',
          password: '',
          confirmPassword: '',
          fullName: ''
        });
      } else {
        const data = await response.json();
        setSignupError(data.detail || 'Signup failed');
      }
    } catch (err) {
      setSignupError('Signup failed. Please try again.');
    }
  };

  // Handle signup input changes
  const handleSignupChange = (e) => {
    const { name, value } = e.target;
    setSignupData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle drag-and-drop file selection
  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setMessage(`Selected file: ${e.dataTransfer.files[0].name}`);
    }
  };

  // Handle AI chat submit
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    setAiLoading(true);
    setChatHistory([...chatHistory, { role: 'user', content: chatInput }]);
    try {
      const response = await fetch('http://localhost:8000/ai_query/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: chatInput }),
      });
      const data = await response.json();
      setChatHistory((prev) => [
        ...prev,
        { role: 'assistant', content: data.sql + (data.result ? `\n${data.result}` : '') }
      ]);
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        { role: 'assistant', content: 'Error contacting AI.' }
      ]);
    }
    setChatInput('');
    setAiLoading(false);
  };

  // Handle file input selection
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setMessage(`Selected file: ${e.target.files[0].name}`);
    }
  };

  // Handle file upload and processing
  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setMessage('Uploading and processing...');
    setCleanedData(null);
    setErrors(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await fetch('http://localhost:8000/upload_sales_data/', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': 'Basic ' + btoa(username + ':' + password)
        }
      });
      const data = await response.json();
      setCleanedData(data.cleaned_data);
      setErrors(data.errors);
      setMessage('Upload and processing complete!');
    } catch (err) {
      setMessage('Error uploading or processing file.');
    }
    setUploading(false);
  };

  if (!loggedIn) {
    return (
      <div className="login-container">
        <div className="login-box">
          <h1>Warehouse Management System</h1>
          <h2>{showSignup ? 'Create Account' : 'Welcome Back'}</h2>
          
          {showSignup ? (
            <form onSubmit={handleSignup} className="signup-form">
              <div className="form-group">
                <input
                  type="text"
                  name="fullName"
                  placeholder="Full Name"
                  value={signupData.fullName}
                  onChange={handleSignupChange}
                  required
                />
              </div>
              <div className="form-group">
                <input
                  type="email"
                  name="email"
                  placeholder="Email"
                  value={signupData.email}
                  onChange={handleSignupChange}
                  required
                />
              </div>
              <div className="form-group">
                <input
                  type="password"
                  name="password"
                  placeholder="Password"
                  value={signupData.password}
                  onChange={handleSignupChange}
                  required
                />
              </div>
              <div className="form-group">
                <input
                  type="password"
                  name="confirmPassword"
                  placeholder="Confirm Password"
                  value={signupData.confirmPassword}
                  onChange={handleSignupChange}
                  required
                />
              </div>
              <button type="submit" className="signup-button">Create Account</button>
              <p className="switch-form">
                Already have an account?{' '}
                <button
                  type="button"
                  className="switch-button"
                  onClick={() => setShowSignup(false)}
                >
                  Sign In
                </button>
              </p>
            </form>
          ) : (
            <form onSubmit={handleLogin} className="login-form">
              <div className="form-group">
                <input
                  type="text"
                  placeholder="Username"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                />
              </div>
              <button type="submit" className="login-button">Sign In</button>
              <p className="switch-form">
                Don't have an account?{' '}
                <button
                  type="button"
                  className="switch-button"
                  onClick={() => setShowSignup(true)}
                >
                  Sign Up
                </button>
              </p>
            </form>
          )}
          {(loginError || signupError) && (
            <p className="error-message">{loginError || signupError}</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <nav className="top-nav">
        <div className="nav-left">
          <h1>Warehouse Management System</h1>
        </div>
        <div className="nav-right">
          <span className="user-welcome">Welcome, {username}</span>
          <button className="logout-button" onClick={() => setLoggedIn(false)}>Logout</button>
        </div>
      </nav>

      <div className="main-content">
        <div className="dashboard-grid">
          {/* Left Column - Data Management */}
          <div className="dashboard-column">
            <div className="upload-section">
              <div className="section-header">
                <h2>Data Management</h2>
                <p className="section-description">Upload and process your sales data</p>
              </div>
              <div
                className="drop-zone"
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
              >
                <div className="drop-zone-content">
                  <i className="upload-icon">📁</i>
                  <p>Drag and drop your sales data file here, or</p>
                  <label className="file-input-label">
                    Choose File
                    <input type="file" onChange={handleFileChange} className="file-input" />
                  </label>
                </div>
              </div>
              <button 
                onClick={handleUpload} 
                disabled={!file || uploading}
                className={`upload-button ${!file || uploading ? 'disabled' : ''}`}
              >
                {uploading ? 'Uploading...' : 'Upload & Clean Data'}
              </button>
              {message && <p className="status-message">{message}</p>}
            </div>

            {errors && errors.length > 0 && (
              <div className="error-section">
                <div className="section-header">
                  <h3>Mapping Errors</h3>
                  <p className="section-description">Issues found during data processing</p>
                </div>
                <div className="error-list">
                  {errors.map((err, idx) => (
                    <div key={idx} className="error-item">{err}</div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Middle Column - Data Preview */}
          <div className="dashboard-column">
            {cleanedData && (
              <div className="data-preview-section">
                <div className="section-header">
                  <h2>Data Preview</h2>
                  <p className="section-description">First 10 rows of processed data</p>
                </div>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        {Object.keys(cleanedData[0] || {}).map((col) => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {cleanedData.slice(0, 10).map((row, idx) => (
                        <tr key={idx}>
                          {Object.values(row).map((val, i) => (
                            <td key={i}>{val}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="preview-note">Showing first 10 rows of {cleanedData.length} total records</p>
              </div>
            )}

            <div className="dashboard-section">
              <div className="section-header">
                <h2>Analytics Dashboard</h2>
                <p className="section-description">View detailed analytics and reports</p>
              </div>
              <div className="dashboard-actions">
                <a
                  href="https://baserow.io/public/grid/88RLy_64wdmhL3iymIeaZXutygoeoFYXnC3zHDoBYJE"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="dashboard-link"
                >
                  Open Live Dashboard
                </a>
                <button className="dashboard-button">
                  Generate Report
                </button>
              </div>
            </div>
          </div>

          {/* Right Column - AI Assistant */}
          <div className="dashboard-column">
            <div className="ai-chat-section">
              <div className="section-header">
                <h2>AI Assistant</h2>
                <p className="section-description">Ask questions about your data</p>
              </div>
              <div className="chat-container">
                <div className="chat-history">
                  {chatHistory.length === 0 ? (
                    <div className="chat-welcome">
                      <h3>Welcome to AI Assistant</h3>
                      <p>Ask me anything about your data, and I'll help you analyze it.</p>
                      <ul className="chat-suggestions">
                        <li>What are the top selling products?</li>
                        <li>Show me sales trends by region</li>
                        <li>Calculate total revenue by category</li>
                      </ul>
                    </div>
                  ) : (
                    chatHistory.map((msg, idx) => (
                      <div key={idx} className={`chat-message ${msg.role}`}>
                        <div className="message-content">
                          <strong>{msg.role === 'user' ? 'You' : 'AI'}:</strong>
                          <p>{msg.content}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                <form onSubmit={handleChatSubmit} className="chat-form">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={e => setChatInput(e.target.value)}
                    placeholder="Ask a question about your data..."
                    disabled={aiLoading}
                    className="chat-input"
                  />
                  <button 
                    type="submit" 
                    disabled={aiLoading || !chatInput.trim()}
                    className={`chat-submit ${aiLoading ? 'loading' : ''}`}
                  >
                    {aiLoading ? 'Thinking...' : 'Ask'}
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
