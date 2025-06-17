import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import MermaidGraph from './MermaidGraph';
import './App.css';

function App() {
  const [target, setTarget] = useState('');
  const [context, setContext] = useState('');
  const [currentView, setCurrentView] = useState('form'); // 'form', 'in-progress', 'report'
  const [investigationId, setInvestigationId] = useState(null);
  const [investigationData, setInvestigationData] = useState(null);
  const [error, setError] = useState('');

  const handleInvestigate = async () => {
    if (!target.trim()) return;

    setError('');
    setCurrentView('in-progress');
    
    try {
      // Create the research query
      const researchQuery = context.trim() 
        ? `Research and investigate: ${target}. Additional context: ${context}`
        : `Research and investigate: ${target}`;

      const response = await axios.post('http://localhost:8001/chat', {
        message: researchQuery,
        max_steps: 3
      });

      // Simulate investigation data structure
      const simulatedData = {
        target: target,
        context: context,
        status: 'completed',
        report: response.data.response,
        sources: response.data.sources || [],
        notes: response.data.notes || [],
        step_count: response.data.step_count || 1
      };

      setInvestigationData(simulatedData);
      setCurrentView('report');
    } catch (error) {
      console.error('Error starting investigation:', error);
      setError('Failed to start investigation. Please try again.');
      setCurrentView('form');
    }
  };

  // Simple timeout for in-progress view simulation
  useEffect(() => {
    let timeout;
    if (currentView === 'in-progress') {
      timeout = setTimeout(() => {
        // This will be handled by the API call completion
      }, 1000);
    }
    return () => {
      if (timeout) clearTimeout(timeout);
    };
  }, [currentView]);

  const handleNewSearch = () => {
    setTarget('');
    setContext('');
    setCurrentView('form');
    setInvestigationId(null);
    setInvestigationData(null);
    setError('');
  };

  const renderForm = () => (
    <div className="investigation-container">
      <div className="form-section">
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        
        <div className="form-group">
          <label htmlFor="target">Investigation Target *</label>
          <input
            id="target"
            type="text"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder="Enter target name, username, email, or identifier..."
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="context">Additional Context</label>
          <textarea
            id="context"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Provide any additional context that may be relevant to the investigation..."
          />
        </div>
        
        <button 
          className="investigate-btn"
          onClick={handleInvestigate} 
          disabled={!target.trim()}
        >
          Investigate
        </button>
      </div>
    </div>
  );

  const renderInProgress = () => (
    <div className="investigation-container">
      <div className="progress-section">
        <h2>Investigation in Progress</h2>
        <div className="target-info">
          <strong>Target:</strong> {target}
          {context && (
            <div><strong>Context:</strong> {context}</div>
          )}
        </div>
        
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Analyzing OSINT sources and generating intelligence report...</p>
          <div style={{ fontSize: '14px', color: '#666', marginTop: '10px' }}>
            • Searching public records<br/>
            • Analyzing social media presence<br/>
            • Cross-referencing data sources<br/>
            • Generating comprehensive report
          </div>
        </div>
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
      </div>
    </div>
  );

  const renderReport = () => (
    <div className="investigation-container">
      <div className="report-section">
        <div className="report-header">
          <h2>Investigation Complete</h2>
          <button className="new-search-btn" onClick={handleNewSearch}>
            New Search
          </button>
        </div>
        
        <div className="target-info">
          <strong>Target:</strong> {investigationData?.target}
          {investigationData?.context && (
            <div><strong>Context:</strong> {investigationData.context}</div>
          )}
        </div>
        
        <div className="report-content">
          <div className="markdown-content">
            <ReactMarkdown>{investigationData?.report || 'No report generated.'}</ReactMarkdown>
          </div>
          
          {investigationData?.sources && investigationData.sources.length > 0 && (
            <div className="sources-section">
              <h3>Sources Analyzed</h3>
              <ul>
                {investigationData.sources.map((source, index) => (
                  <li key={index}>{source}</li>
                ))}
              </ul>
            </div>
          )}
          
          {investigationData?.notes && investigationData.notes.length > 0 && (
            <div className="notes-section">
              <h3>Research Notes</h3>
              <ul>
                {investigationData.notes.map((note, index) => (
                  <li key={index}>{note}</li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="meta-info">
            <small>Research completed in {investigationData?.step_count || 1} step(s)</small>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="App">
      <header className="App-header">
        <h1>AutoSpook</h1>
        <p>OSINT Investigation Tool</p>
      </header>
      
      {currentView === 'form' && renderForm()}
      {currentView === 'in-progress' && renderInProgress()}
      {currentView === 'report' && renderReport()}
    </div>
  );
}

export default App; 