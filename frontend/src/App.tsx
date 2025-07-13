import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = 'http://localhost:8000';

interface QuickInsight {
  metric: string;
  value: string;
  trend: string;
}

interface AnalysisResult {
  analysis_id: string;
  query: string;
  status: string;
  results?: {
    data: any;
    analysis: string;
    recommendations: string;
  };
}

function QuickInsights() {
  const [insights, setInsights] = useState<QuickInsight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: add retry logic if this fails
    axios.get(`${API_BASE}/quick-insights`)
      .then(response => {
        console.log('Got insights:', response.data);
        setInsights(response.data.insights);
        setLoading(false);
      })
      .catch(error => {
        console.error('Failed to fetch insights:', error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <div className="loading-text">Loading insights...</div>
      </div>
    );
  }

  return (
    <div className="insights-grid">
      {insights.map((insight, i) => (
        <div key={i} className="insight-card">
          <div className="card-accent"></div>
          <div className="metric-label">{insight.metric}</div>
          <div className="metric-value">{insight.value}</div>
          <div className="metric-trend">
            <span>▲</span> {insight.trend}
          </div>
        </div>
      ))}
    </div>
  );
}

function AnalysisChat() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError('');
    setResult(null);

    try {
      console.log('Sending query:', query);
      const response = await axios.post(`${API_BASE}/analyze`, { query });
      setResult(response.data);
      console.log('Analysis complete:', response.data);
    } catch (err) {
      console.error('Analysis failed:', err);
      setError('Something went wrong. Try again?');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="analysis-container">
      <div className="query-box">
        <div className="input-group">
          <input
            type="text"
            placeholder="Ask about your e-commerce data..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            className="query-input"
          />
          <button
            onClick={handleSubmit}
            disabled={loading}
            className={`analyze-btn ${loading ? 'loading' : ''}`}
          >
            {loading ? (
              <span className="btn-loading">
                <div className="btn-spinner"></div>
                Analyzing...
              </span>
            ) : 'Analyze'}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-box">
          <span>⚠</span> {error}
        </div>
      )}

      {result && (
        <div className="results-panel">
          <div className="results-header">
            <div className="query-title">Query: {result.query}</div>
            <span className="status-badge">{result.status}</span>
          </div>

          {result.results && (
            <div className="results-content">
              <div className="result-section">
                <h3>Analysis</h3>
                <div className="result-text">
                  {result.results.analysis}
                </div>
              </div>

              <div className="result-section">
                <h3>Recommendations</h3>
                <div className="result-text">
                  {result.results.recommendations}
                </div>
              </div>

              <div className="result-section">
                <h3>Raw Data</h3>
                <div className="raw-data">
                  <pre>{JSON.stringify(result.results.data, null, 2)}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function App() {
  const [activeTab, setActiveTab] = useState('insights');

  return (
    <div className="app">
      <div className="background-effects"></div>
      
      <div className="container">
        <header className="header">
          <h1 className="title">E-COMMERCE AI ANALYZER</h1>
          <p className="subtitle">
            AI-powered insights from your Snowflake data warehouse
          </p>
        </header>

        <div className="tab-nav">
          <div className="tab-container">
            <button
              onClick={() => setActiveTab('insights')}
              className={`tab ${activeTab === 'insights' ? 'active' : ''}`}
            >
              Quick Insights
            </button>
            <button
              onClick={() => setActiveTab('analysis')}
              className={`tab ${activeTab === 'analysis' ? 'active' : ''}`}
            >
              AI Analysis
            </button>
          </div>
        </div>

        <main className="content">
          {activeTab === 'insights' && <QuickInsights />}
          {activeTab === 'analysis' && <AnalysisChat />}
        </main>
      </div>
    </div>
  );
}

export default App;