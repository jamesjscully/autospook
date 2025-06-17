import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

const MermaidGraph = ({ chart, id = 'mermaid-graph' }) => {
  const chartRef = useRef();
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Initialize mermaid with configuration
    try {
      mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'loose',
        fontFamily: 'Segoe UI, system-ui, -apple-system, sans-serif',
        flowchart: {
          useMaxWidth: true,
          htmlLabels: true,
          curve: 'basis'
        }
      });
      setIsInitialized(true);
    } catch (err) {
      console.error('Mermaid initialization error:', err);
      setError('Failed to initialize mermaid');
    }
  }, []);

  useEffect(() => {
    const renderChart = async () => {
      if (!chart || !chartRef.current || !isInitialized) {
        return;
      }

      try {
        // Clear previous content
        chartRef.current.innerHTML = '';
        
        // Create a unique ID for this render
        const graphId = `${id}-${Date.now()}`;
        
        // Create a temporary div for rendering
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = `<div class="mermaid">${chart}</div>`;
        chartRef.current.appendChild(tempDiv);
        
        // Use mermaid.run() for newer versions
        if (typeof mermaid.run === 'function') {
          await mermaid.run({
            nodes: chartRef.current.querySelectorAll('.mermaid')
          });
        } else {
          // Fallback for older versions
          const { svg } = await mermaid.render(graphId, chart);
          chartRef.current.innerHTML = svg;
        }
        
        setError(null);
      } catch (err) {
        console.error('Mermaid rendering error:', err);
        setError('Error rendering graph');
        chartRef.current.innerHTML = `<div style="padding: 20px; text-align: center; color: #721c24;">
          <p>Error rendering workflow graph</p>
          <small>Check console for details: ${err.message}</small>
        </div>`;
      }
    };

    renderChart();
  }, [chart, id, isInitialized]);

  if (!isInitialized) {
    return (
      <div className="mermaid-container" style={{ 
        width: '100%', 
        minHeight: '400px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        <div>Initializing graph...</div>
      </div>
    );
  }

  return (
    <div 
      ref={chartRef} 
      className="mermaid-container"
      style={{ 
        width: '100%', 
        minHeight: '400px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      }}
    />
  );
};

export default MermaidGraph;