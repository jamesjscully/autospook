import React, { useState } from "react";
import { QueryInterface } from "./QueryInterface";
import { InvestigationProgress } from "./InvestigationProgress";
import { ReportViewer } from "./ReportViewer";
import { SourceExplorer } from "./SourceExplorer";
import { EntityGraph } from "./EntityGraph";
import { useInvestigation } from "@/contexts/InvestigationContext";
import { Shield, Search, FileText, Database, Network, Activity } from "lucide-react";

export const OSINTDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("query");
  const { investigation, isLoading } = useInvestigation();

  const tabs = [
    { id: "query", label: "New Investigation", icon: Search },
    { id: "progress", label: "Progress", icon: Activity },
    { id: "entities", label: "Entity Graph", icon: Network },
    { id: "sources", label: "Sources", icon: Database },
    { id: "report", label: "Report", icon: FileText },
  ];

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Shield className="w-8 h-8 text-cyan-500" />
            <div>
              <h1 className="text-2xl font-bold text-white">AutoSpook OSINT</h1>
              <p className="text-sm text-gray-400">Multi-Agent Intelligence System</p>
            </div>
          </div>
          {investigation && (
            <div className="text-sm text-gray-400">
              Investigation ID: <span className="font-mono text-cyan-500">{investigation.id}</span>
            </div>
          )}
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-gray-900 border-b border-gray-800 px-6">
        <div className="flex space-x-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? "border-cyan-500 text-cyan-500"
                    : "border-transparent text-gray-400 hover:text-gray-300"
                }`}
                disabled={!investigation && tab.id !== "query"}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden bg-gray-950">
        <div className="h-full p-6">
          {activeTab === "query" && <QueryInterface />}
          {activeTab === "progress" && <InvestigationProgress />}
          {activeTab === "entities" && <EntityGraph />}
          {activeTab === "sources" && <SourceExplorer />}
          {activeTab === "report" && <ReportViewer />}
        </div>
      </main>

      {/* Status Bar */}
      {isLoading && (
        <div className="bg-gray-900 border-t border-gray-800 px-6 py-2">
          <div className="flex items-center space-x-2">
            <div className="animate-pulse w-2 h-2 bg-cyan-500 rounded-full"></div>
            <span className="text-sm text-gray-400">Investigation in progress...</span>
          </div>
        </div>
      )}
    </div>
  );
}; 