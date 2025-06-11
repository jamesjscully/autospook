import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from "react";

export interface OSINTEntity {
  id: string;
  type: "person" | "organization" | "location" | "event" | "object";
  name: string;
  attributes: Record<string, any>;
  confidence: number;
  sources: string[];
}

export interface Investigation {
  id: string;
  query: string;
  entities: OSINTEntity[];
  sources: any[];
  report?: any;
  timeline: any[];
  pivots: any[];
  status: "planning" | "retrieving" | "analyzing" | "reporting" | "complete";
  progress: number;
}

interface InvestigationContextType {
  investigation: Investigation | null;
  isLoading: boolean;
  error: string | null;
  startInvestigation: (query: string, settings: any) => void;
  clearInvestigation: () => void;
}

const InvestigationContext = createContext<InvestigationContextType | undefined>(undefined);

export const InvestigationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const apiUrl = import.meta.env.DEV ? "http://localhost:2024" : "http://localhost:8123";

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const connectWebSocket = (investigationId: string) => {
    const wsUrl = apiUrl.replace('http', 'ws') + `/ws/${investigationId}`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected for investigation:', investigationId);
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleRealtimeUpdate(data);
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
    };
  };

  const handleRealtimeUpdate = (event: any) => {
    if (event.type === 'query_analysis') {
      setInvestigation(prev => ({
        ...prev!,
        entities: event.entities || [],
        status: "planning"
      }));
    } else if (event.type === 'retrieval_progress') {
      setInvestigation(prev => ({
        ...prev!,
        sources: [...(prev?.sources || []), ...(event.sources || [])],
        progress: (event.completed / event.total) * 100,
        status: "retrieving"
      }));
    } else if (event.type === 'pivot_analysis') {
      setInvestigation(prev => ({
        ...prev!,
        pivots: [...(prev?.pivots || []), { angles: event.new_angles }],
        status: "analyzing"
      }));
    } else if (event.type === 'report_generation') {
      setInvestigation(prev => ({
        ...prev!,
        report: event.report,
        status: "reporting"
      }));
    } else if (event.type === 'quality_assessment') {
      setInvestigation(prev => ({
        ...prev!,
        status: "complete",
        progress: 100
      }));
    }
  };

  const pollInvestigationStatus = async (investigationId: string) => {
    try {
      const response = await fetch(`${apiUrl}/api/investigations/${investigationId}`);
      if (!response.ok) throw new Error('Failed to fetch status');
      
      const status = await response.json();
      
      setInvestigation(prev => ({
        ...prev!,
        status: status.status,
        progress: status.progress,
        entities: prev?.entities || []
      }));

      // Fetch entities
      const entitiesResponse = await fetch(`${apiUrl}/api/investigations/${investigationId}/entities`);
      if (entitiesResponse.ok) {
        const entitiesData = await entitiesResponse.json();
        setInvestigation(prev => ({
          ...prev!,
          entities: entitiesData.entities
        }));
      }

      // Fetch sources
      const sourcesResponse = await fetch(`${apiUrl}/api/investigations/${investigationId}/sources`);
      if (sourcesResponse.ok) {
        const sourcesData = await sourcesResponse.json();
        setInvestigation(prev => ({
          ...prev!,
          sources: sourcesData.sources
        }));
      }

      // If complete, fetch report
      if (status.status === 'complete') {
        const reportResponse = await fetch(`${apiUrl}/api/investigations/${investigationId}/report`);
        if (reportResponse.ok) {
          const reportData = await reportResponse.json();
          setInvestigation(prev => ({
            ...prev!,
            report: reportData.report
          }));
        }
        
        // Stop polling
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
        }
      }
    } catch (err) {
      console.error('Error polling status:', err);
    }
  };

  const startInvestigation = useCallback(async (query: string, settings: any) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Create investigation via API
      const response = await fetch(`${apiUrl}/api/investigations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          max_retrievals: settings.maxRetrievals || 12,
          focus_areas: settings.focusAreas || [],
          entity_types: settings.entityTypes || []
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start investigation');
      }

      const data = await response.json();
      const investigationId = data.investigation_id;

      // Create initial investigation object
      const newInvestigation: Investigation = {
        id: investigationId,
        query,
        entities: [],
        sources: [],
        timeline: [],
        pivots: [],
        status: "planning",
        progress: 0
      };
      
      setInvestigation(newInvestigation);

      // Connect WebSocket for real-time updates
      connectWebSocket(investigationId);

      // Start polling as backup
      pollingIntervalRef.current = setInterval(() => {
        pollInvestigationStatus(investigationId);
      }, 2000);

    } catch (err: any) {
      setError(err.message || 'Failed to start investigation');
      setIsLoading(false);
    }
  }, [apiUrl]);

  const clearInvestigation = useCallback(() => {
    setInvestigation(null);
    setError(null);
    setIsLoading(false);
    
    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    // Stop polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  return (
    <InvestigationContext.Provider
      value={{
        investigation,
        isLoading,
        error,
        startInvestigation,
        clearInvestigation,
      }}
    >
      {children}
    </InvestigationContext.Provider>
  );
};

export const useInvestigation = () => {
  const context = useContext(InvestigationContext);
  if (!context) {
    throw new Error("useInvestigation must be used within InvestigationProvider");
  }
  return context;
}; 