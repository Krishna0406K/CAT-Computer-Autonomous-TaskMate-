import { useState, useRef, useEffect } from 'react';
import './App.css';
import ObservatoryDashboard from './components/ObservatoryDashboard';

function App() {
  const [messages, setMessages] = useState([{ role: 'agent', content: 'Ready! What would you like to do?' }]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [currentState, setCurrentState] = useState(null);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [voiceState, setVoiceState] = useState('IDLE');
  const [showDashboard, setShowDashboard] = useState(false);
  const [showObservatory, setShowObservatory] = useState(false);
  const [telemetry, setTelemetry] = useState(null);
  const [showQR, setShowQR] = useState(false);
  const [mobileUrl, setMobileUrl] = useState('');
  
  // Microphone State
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking, pendingApprovals]);

  // Server-Sent Events (SSE) Listener for Background Voice Commands & State
  useEffect(() => {
    const eventSource = new EventSource("http://localhost:8000/voice_stream");
    eventSource.onmessage = (event) => {
      const command = event.data;
      window.dispatchEvent(new CustomEvent('voice-command', { detail: command }));
    };
    
    const stateSource = new EventSource("http://localhost:8000/voice_state_stream");
    stateSource.onmessage = (event) => {
      setVoiceState(event.data);
    };
    
    return () => {
      eventSource.close();
      stateSource.close();
    };
  }, []);

  useEffect(() => {
    const listener = (e) => {
      const command = e.detail;
      if (!isThinking && pendingApprovals.length === 0) {
        setMessages(prev => [...prev, { role: 'user', content: command }]);
        sendRequest({ task: command, state: null });
      }
    };
    window.addEventListener('voice-command', listener);
    return () => window.removeEventListener('voice-command', listener);
  }, [isThinking, pendingApprovals]);

  useEffect(() => {
    const fetchNetworkInfo = async () => {
      try {
        const res = await fetch("http://localhost:8000/network_info");
        const data = await res.json();
        setMobileUrl(data.mobile_url);
      } catch (err) {
        console.error("Failed to fetch network info", err);
      }
    };
    fetchNetworkInfo();
  }, []);

  const loadDashboard = async () => {
    try {
      const res = await fetch("http://localhost:8000/voice_telemetry");
      const data = await res.json();
      setTelemetry(data);
      setShowDashboard(true);
    } catch (e) {
      console.error(e);
    }
  };

  const handleMicrophone = async () => {
    if (isRecording) {
      if (mediaRecorderRef.current) mediaRecorderRef.current.stop();
      setIsRecording(false);
      return;
    }
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append("file", audioBlob, "voice_input.webm");

        try {
          const res = await fetch("http://localhost:8000/transcribe", { method: "POST", body: formData });
          const data = await res.json();
          if (data.text) setInput(data.text);
        } catch (e) {
          console.error("Transcription failed", e);
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access denied", err);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isThinking || pendingApprovals.length > 0) return;
    
    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    
    await sendRequest({ task: userMsg, state: null });
  };

  const handleStop = async () => {
    try {
      await fetch("http://localhost:8000/cancel", { method: "POST" });
    } catch (err) {
      console.error("Failed to cancel:", err);
    }
  };

  const sendRequest = async (payload) => {
    setIsThinking(true);
    try {
      const res = await fetch("http://localhost:8000/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      
      if (data.status === "approval_required") {
        setCurrentState(data.state);
        setPendingApprovals(data.state.pending_approvals || []);
      } else {
        setMessages(prev => [...prev, { role: 'agent', content: data.final_response }]);
        setCurrentState(null);
        setPendingApprovals([]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'agent', content: `[Error communicating with Gateway]: ${err.message}` }]);
    }
    setIsThinking(false);
  };

  const handleApproval = async (approved) => {
    if (!currentState) return;
    
    const decision = approved ? "approved" : "denied";
    const updatedState = { ...currentState };
    
    // Update all pending tools with the decision
    updatedState.pending_approvals = updatedState.pending_approvals.map(p => ({
      ...p,
      status: decision
    }));

    setPendingApprovals([]);
    
    // Resume agent with the updated state
    await sendRequest({ 
      task: currentState.task, 
      state: updatedState 
    });
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo">
          <img src="/desktop_icon.png" alt="CAT Logo" />
        </div>
        <h1>CAT <span>Desktop Shell</span></h1>
        
        <div className="header-actions" style={{ display: 'flex', alignItems: 'center', gap: '15px', marginLeft: 'auto', marginRight: '15px' }}>
              <button onClick={() => setShowQR(true)} style={{ background: 'transparent', border: '1px solid #3b82f6', borderRadius: '4px', cursor: 'pointer', padding: '5px 10px', color: '#3b82f6', fontWeight: 'bold' }}>📱 Mobile Connect</button>
            <button onClick={() => setShowObservatory(true)} style={{ background: 'transparent', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer', padding: '5px 10px', color: 'white' }}>Observatory</button><button onClick={loadDashboard} style={{ background: 'transparent', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer', padding: '5px 10px' }}>
              📊 Dashboard
            </button>
            <div className={`status-indicator ${isThinking ? 'working' : 'idle'}`}>
              {isThinking ? 'Hunting...' : (voiceState !== 'IDLE' ? voiceState : 'Purring (Idle)')}
            </div>
        </div>
      </header>

            {showQR && (
        <div className="modal-overlay" onClick={() => setShowQR(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{textAlign: 'center'}}>
            <h2>?? Connect Mobile App</h2>
            <p style={{margin: '15px 0', color: '#ccc'}}>Scan this QR code with your phone camera:</p>
            <div style={{background: 'white', padding: '15px', borderRadius: '10px', display: 'inline-block', marginBottom: '20px'}}>
              <img src={`https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(mobileUrl)}`} alt="QR Code" width="250" height="250" />
            </div>
            <p style={{fontSize: '12px', color: '#888', wordBreak: 'break-all'}}>{mobileUrl}</p>
            <div className="modal-actions" style={{justifyContent: 'center', marginTop: '20px'}}>
              <button className="btn-allow" onClick={() => setShowQR(false)}>Done</button>
            </div>
          </div>
        </div>
      )}
      {showObservatory && <ObservatoryDashboard onClose={() => setShowObservatory(false)} />}
      
      <main className="chat-window">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <div className="message-avatar">
              {m.role === 'user' ? '👤' : <img src="/desktop_icon.png" alt="CAT" />}
            </div>
            <div className="message-content">{m.content}</div>
          </div>
        ))}
        
        {isThinking && !pendingApprovals.length && (
          <div className="message agent thinking">
            <div className="message-avatar">
              <img src="/desktop_icon.png" alt="CAT" />
            </div>
            <div className="typing-indicator"><span>🐾</span><span>🐾</span><span>🐾</span></div>
          </div>
        )}
        
        <div ref={chatEndRef} />
      </main>

      {/* Voice Telemetry Dashboard Modal */}
      {showDashboard && telemetry && (
        <div className="modal-overlay" onClick={() => setShowDashboard(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-icon">📊</div>
            <h2>Voice Health Dashboard</h2>
            <div className="tool-list" style={{ marginTop: '15px' }}>
              <div className="tool-card">
                <div className="tool-header"><span className="tool-name">Voice Commands</span></div>
                <pre className="tool-args">Total: {telemetry.total_commands} | Success Rate: {telemetry.success_rate}</pre>
              </div>
              <div className="tool-card">
                <div className="tool-header"><span className="tool-name">Performance</span></div>
                <pre className="tool-args">Avg STT Latency: {telemetry.avg_stt_latency_ms}ms</pre>
              </div>
              <div className="tool-card">
                <div className="tool-header"><span className="tool-name">Diagnostics</span></div>
                <pre className="tool-args">Wake Activations: {telemetry.wake_activations} | Filtered Hallucinations: {telemetry.empty_transcriptions}</pre>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn-allow" onClick={() => setShowDashboard(false)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Permission Modal */}
      {pendingApprovals.length > 0 && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-icon">🙀</div>
            <h2>Action Required</h2>
            <p>CAT has found something <strong>HIGH RISK</strong> and needs permission to pounce:</p>
            <div className="tool-list">
              {pendingApprovals.map((tool, idx) => (
                <div key={idx} className="tool-card">
                  <div className="tool-header">
                    <span className="tool-name">{tool.name}</span>
                    <span className="tool-risk">{tool.risk}</span>
                  </div>
                  <pre className="tool-args">{JSON.stringify(tool.args, null, 2)}</pre>
                </div>
              ))}
            </div>
            <div className="modal-actions">
              <button className="btn-deny" onClick={() => handleApproval(false)}>Hiss (Deny)</button>
              <button className="btn-allow" onClick={() => handleApproval(true)}>Pounce (Allow)</button>
            </div>
          </div>
        </div>
      )}

      <footer className="input-area">
        <button 
          className={`btn-mic ${isRecording ? 'recording' : ''}`}
          onClick={handleMicrophone}
          disabled={isThinking || pendingApprovals.length > 0}
          title={isRecording ? "Click to stop recording" : "Click to speak"}
        >
          {isRecording ? "🛑" : "🎤"}
        </button>
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={isRecording ? "Listening... click stop when done" : "Tell CAT what to do..."}
          disabled={isThinking || pendingApprovals.length > 0 || isRecording}
        />
        {isThinking ? (
          <button className="btn-stop" onClick={handleStop}>Stop</button>
        ) : (
          <button 
            onClick={handleSend} 
            disabled={pendingApprovals.length > 0 || !input.trim() || isRecording}
          >
            Send
          </button>
        )}
      </footer>
    </div>
  );
}

export default App;
