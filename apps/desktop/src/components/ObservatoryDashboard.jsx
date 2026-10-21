import React, { useState, useEffect } from 'react';

const ObservatoryDashboard = ({ onClose }) => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch('http://localhost:8000/observatory/metrics');
        const data = await res.json();
        setMetrics(data);
      } catch (err) {
        console.error("Failed to fetch observatory metrics:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="observatory-overlay">
        <div className="observatory-modal">
          <div className="loader">Loading telemetry...</div>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="observatory-overlay">
        <div className="observatory-modal">
          <h2>Error loading metrics</h2>
          <button className="btn-close" onClick={onClose}>Close</button>
        </div>
      </div>
    );
  }

  return (
    <div className="observatory-overlay">
      <div className="observatory-modal">
        <div className="obs-header">
          <h2>🔭 Observatory Overview</h2>
          <button className="btn-close" onClick={onClose}>X</button>
        </div>

        <div className="metrics-grid">
          <div className="metric-card">
            <h3>Today's Tasks</h3>
            <div className="metric-value">{metrics.today_tasks}</div>
            <div className="metric-sub">Total: {metrics.total_tasks}</div>
          </div>
          <div className="metric-card">
            <h3>Success Rate</h3>
            <div className="metric-value">{metrics.success_rate}</div>
            <div className="metric-sub">Across all time</div>
          </div>
          <div className="metric-card">
            <h3>Avg. Execution</h3>
            <div className="metric-value">{metrics.avg_execution_time}</div>
            <div className="metric-sub">Per task completed</div>
          </div>
        </div>

        <div className="system-metrics">
          <h3>System Health (Local)</h3>
          <div className="sys-bars">
            <div className="sys-bar">
              <label>CPU Usage ({metrics.system_metrics.cpu_percent}%)</label>
              <div className="progress-bg">
                <div className="progress-fill" style={{ width: `${metrics.system_metrics.cpu_percent}%`, backgroundColor: metrics.system_metrics.cpu_percent > 80 ? 'red' : '#4caf50' }}></div>
              </div>
            </div>
            <div className="sys-bar">
              <label>RAM Usage ({metrics.system_metrics.ram_used_gb}GB / {metrics.system_metrics.ram_total_gb}GB)</label>
              <div className="progress-bg">
                <div className="progress-fill" style={{ width: `${metrics.system_metrics.ram_percent}%`, backgroundColor: metrics.system_metrics.ram_percent > 80 ? 'red' : '#2196f3' }}></div>
              </div>
            </div>
          </div>
        </div>

        <div className="recent-tasks">
          <h3>Recent Tasks</h3>
          <table className="task-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Task</th>
                  <th>Status</th>
                  <th>Duration</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {metrics.recent_tasks.length === 0 ? (
                  <tr><td colSpan="5">No tasks yet.</td></tr>
                ) : (
                  metrics.recent_tasks.map(task => (
                    <tr key={task.id}>
                      <td>#{task.id}</td>
                      <td className="task-prompt">{task.task_prompt}</td>
                      <td>
                        <span className={`status-badge ${task.status.toLowerCase()}`}>
                          {task.status}
                        </span>
                      </td>
                      <td style={{ color: '#aaa', fontSize: '0.9em' }}>
                        {task.duration_seconds > 0 ? `${task.duration_seconds.toFixed(1)}s` : '<1s'}
                      </td>
                      <td className="task-date">{new Date(task.created_at + "Z").toLocaleTimeString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
        </div>
      </div>

      <style>{`
        .observatory-overlay {
          position: fixed;
          top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(0,0,0,0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 2000;
        }
        .observatory-modal {
          background: #1e1e1e;
          width: 80%;
          max-width: 900px;
          border-radius: 12px;
          padding: 24px;
          color: #eee;
          box-shadow: 0 10px 30px rgba(0,0,0,0.5);
          display: flex;
          flex-direction: column;
          gap: 20px;
        }
        .obs-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid #333;
          padding-bottom: 12px;
        }
        .obs-header h2 {
          margin: 0;
          color: #fff;
        }
        .btn-close {
          background: transparent;
          border: none;
          color: #888;
          font-size: 20px;
          cursor: pointer;
        }
        .btn-close:hover { color: #fff; }
        
        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 15px;
        }
        .metric-card {
          background: #2a2a2a;
          padding: 20px;
          border-radius: 8px;
          text-align: center;
          border-top: 3px solid #ff9800;
        }
        .metric-card h3 {
          margin: 0 0 10px 0;
          font-size: 14px;
          color: #aaa;
          text-transform: uppercase;
        }
        .metric-value {
          font-size: 32px;
          font-weight: bold;
          color: #fff;
          margin-bottom: 5px;
        }
        .metric-sub {
          font-size: 12px;
          color: #777;
        }

        .system-metrics {
          background: #2a2a2a;
          padding: 20px;
          border-radius: 8px;
        }
        .system-metrics h3 {
          margin: 0 0 15px 0;
          font-size: 16px;
          border-bottom: 1px solid #444;
          padding-bottom: 5px;
        }
        .sys-bars {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }
        .sys-bar label {
          display: block;
          margin-bottom: 5px;
          font-size: 13px;
        }
        .progress-bg {
          width: 100%;
          height: 8px;
          background: #444;
          border-radius: 4px;
          overflow: hidden;
        }
        .progress-fill {
          height: 100%;
          transition: width 0.3s ease;
        }

        .recent-tasks {
          background: #2a2a2a;
          padding: 20px;
          border-radius: 8px;
          overflow-y: auto;
          max-height: 250px;
        }
        .recent-tasks h3 { margin: 0 0 15px 0; font-size: 16px; border-bottom: 1px solid #444; padding-bottom: 5px; }
        .task-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 13px;
        }
        .task-table th {
          text-align: left;
          padding: 8px;
          color: #aaa;
          border-bottom: 1px solid #444;
        }
        .task-table td {
          padding: 10px 8px;
          border-bottom: 1px solid #333;
        }
        .task-prompt {
          max-width: 300px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .status-badge {
          padding: 3px 8px;
          border-radius: 12px;
          font-size: 11px;
          font-weight: bold;
        }
        .status-badge.success { background: rgba(76, 175, 80, 0.2); color: #4caf50; }
        .status-badge.failed { background: rgba(244, 67, 54, 0.2); color: #f44336; }
        .task-date { color: #888; }
      `}</style>
    </div>
  );
};

export default ObservatoryDashboard;
