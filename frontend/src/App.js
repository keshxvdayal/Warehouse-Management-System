import React, { useState } from 'react';
import './App.css';

function App() {
  // Authentication state
  const [loggedIn, setLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');

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
      <div className="App">
        <h2>Login</h2>
        <form onSubmit={handleLogin} className="login-form">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
          <button type="submit">Login</button>
        </form>
        {loginError && <p className="error-message">{loginError}</p>}
      </div>
    );
  }

  return (
    <div className="App">
      <h2>Sales Data Uploader</h2>
      <div
        className="drop-zone"
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        <p>Drag and drop your sales data file here, or</p>
        <input type="file" onChange={handleFileChange} />
      </div>
      <button onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? 'Uploading...' : 'Upload & Clean Data'}
      </button>
      <p>{message}</p>
      {errors && errors.length > 0 && (
        <div className="error-table">
          <h3>Mapping Errors</h3>
          <ul>
            {errors.map((err, idx) => (
              <li key={idx}>{err}</li>
            ))}
          </ul>
        </div>
      )}
      {cleanedData && (
        <div className="data-table">
          <h3>Cleaned Data Preview</h3>
          <table>
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
          <p>Showing first 10 rows.</p>
        </div>
      )}
      <div className="dashboard-embed">
        <h2>Live Dashboard</h2>
        <a
          href="https://baserow.io/public/grid/88RLy_64wdmhL3iymIeaZXutygoeoFYXnC3zHDoBYJE"
          target="_blank"
          rel="noopener noreferrer"
          className="dashboard-link"
        >
          Open Live Dashboard
        </a>
      </div>
      {/* Add this below the dashboard link */}
  <div className="ai-chat-widget">
    <h2>Ask AI (Natural Language to SQL)</h2>
    <div className="chat-history">
      {chatHistory.map((msg, idx) => (
        <div key={idx} className={msg.role}>
          <strong>{msg.role === 'user' ? 'You' : 'AI'}:</strong> {msg.content}
        </div>
      ))}
    </div>
    <form onSubmit={handleChatSubmit} className="chat-form">
      <input
        type="text"
        value={chatInput}
        onChange={e => setChatInput(e.target.value)}
        placeholder="Ask a question about your data..."
        disabled={aiLoading}
      />
      <button type="submit" disabled={aiLoading || !chatInput.trim()}>
        {aiLoading ? 'Thinking...' : 'Ask'}
      </button>
    </form>
  </div>
    </div>
  );
}

export default App;
