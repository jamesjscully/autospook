import React from "react";
import { useInvestigation } from "@/contexts/InvestigationContext";
import { CheckCircle, Circle, Loader2, AlertCircle } from "lucide-react";

interface AgentStatus {
  name: string;
  agent: string;
  status: "pending" | "running" | "complete" | "error";
  message?: string;
  progress?: number;
}

export const InvestigationProgress: React.FC = () => {
  const { investigation, isLoading } = useInvestigation();

  if (!investigation) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No active investigation</p>
      </div>
    );
  }

  const agents: AgentStatus[] = [
    {
      name: "Query Analysis",
      agent: "Claude Sonnet 4",
      status: investigation.status === "planning" ? "running" : 
              investigation.entities.length > 0 ? "complete" : "pending",
      message: investigation.entities.length > 0 
        ? `Identified ${investigation.entities.length} entities`
        : "Analyzing query and extracting entities..."
    },
    {
      name: "Planning & Orchestration",
      agent: "Claude Sonnet 4",
      status: investigation.status === "planning" && investigation.entities.length > 0 ? "running" :
              investigation.status !== "planning" ? "complete" : "pending",
      message: "Creating retrieval strategy..."
    },
    {
      name: "Multi-Source Retrieval",
      agent: "Claude Sonnet 4",
      status: investigation.status === "retrieving" ? "running" :
              investigation.sources.length > 0 ? "complete" : "pending",
      message: `${investigation.sources.length} sources gathered`,
      progress: investigation.progress
    },
    {
      name: "Pivot Analysis",
      agent: "GPT-4o",
      status: investigation.status === "analyzing" ? "running" :
              investigation.pivots.length > 0 ? "complete" : "pending",
      message: investigation.pivots.length > 0 
        ? `Found ${investigation.pivots.length} new investigation angles`
        : "Analyzing patterns and connections..."
    },
    {
      name: "Report Synthesis",
      agent: "Gemini 1.5 Pro",
      status: investigation.status === "reporting" ? "running" :
              investigation.report ? "complete" : "pending",
      message: investigation.report ? "Report generated" : "Synthesizing findings..."
    },
    {
      name: "Quality Assessment",
      agent: "Claude Opus 4",
      status: investigation.status === "complete" ? "complete" :
              investigation.status === "reporting" && investigation.report ? "running" : "pending",
      message: investigation.status === "complete" ? "Investigation complete" : "Evaluating report quality..."
    }
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "complete":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "running":
        return <Loader2 className="w-5 h-5 text-cyan-500 animate-spin" />;
      case "error":
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Circle className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "complete":
        return "text-green-500";
      case "running":
        return "text-cyan-500";
      case "error":
        return "text-red-500";
      default:
        return "text-gray-600";
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2">Investigation Progress</h2>
        <p className="text-gray-400">Query: "{investigation.query}"</p>
      </div>

      {/* Overall Progress Bar */}
      <div className="bg-gray-900 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Overall Progress</span>
          <span className="text-sm text-gray-400">{Math.round(investigation.progress)}%</span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-2">
          <div
            className="bg-cyan-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${investigation.progress}%` }}
          />
        </div>
      </div>

      {/* Agent Status */}
      <div className="space-y-4">
        {agents.map((agent, idx) => (
          <div key={idx} className="bg-gray-900 rounded-lg p-6">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-3">
                {getStatusIcon(agent.status)}
                <div>
                  <h3 className="font-medium">{agent.name}</h3>
                  <p className="text-sm text-gray-500">Agent: {agent.agent}</p>
                </div>
              </div>
              <span className={`text-sm font-medium ${getStatusColor(agent.status)}`}>
                {agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}
              </span>
            </div>
            
            {agent.message && (
              <p className="text-sm text-gray-400 ml-8">{agent.message}</p>
            )}
            
            {agent.progress !== undefined && agent.status === "running" && (
              <div className="ml-8 mt-2">
                <div className="w-full bg-gray-800 rounded-full h-1">
                  <div
                    className="bg-cyan-500 h-1 rounded-full transition-all duration-500"
                    style={{ width: `${agent.progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Real-time Activity Feed */}
      {investigation.sources.length > 0 && (
        <div className="mt-8 bg-gray-900 rounded-lg p-6">
          <h3 className="font-medium mb-4">Recent Sources</h3>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {investigation.sources.slice(-5).reverse().map((source: any, idx: number) => (
              <div key={idx} className="flex items-center space-x-2 text-sm">
                <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse" />
                <span className="text-gray-400">{source.title || source.url || "Source " + idx}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}; 