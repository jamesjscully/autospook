import React, { useState } from "react";
import { useInvestigation } from "@/contexts/InvestigationContext";
import { Search, Loader2, Target, Globe, Shield, Users } from "lucide-react";

export const QueryInterface: React.FC = () => {
  const [query, setQuery] = useState("");
  const [settings, setSettings] = useState({
    maxRetrievals: 12,
    focusAreas: [] as string[],
    entityTypes: [] as string[]
  });
  
  const { startInvestigation, isLoading } = useInvestigation();

  const focusAreaOptions = [
    { id: "social", label: "Social Media", icon: Users },
    { id: "web", label: "Web Sources", icon: Globe },
    { id: "records", label: "Public Records", icon: Shield },
    { id: "academic", label: "Academic Sources", icon: Target },
  ];

  const entityTypeOptions = [
    { id: "person", label: "Person" },
    { id: "organization", label: "Organization" },
    { id: "location", label: "Location" },
    { id: "event", label: "Event" },
  ];

  const toggleFocusArea = (area: string) => {
    setSettings(prev => ({
      ...prev,
      focusAreas: prev.focusAreas.includes(area)
        ? prev.focusAreas.filter(a => a !== area)
        : [...prev.focusAreas, area]
    }));
  };

  const toggleEntityType = (type: string) => {
    setSettings(prev => ({
      ...prev,
      entityTypes: prev.entityTypes.includes(type)
        ? prev.entityTypes.filter(t => t !== type)
        : [...prev.entityTypes, type]
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      startInvestigation(query, settings);
    }
  };

  const exampleQueries = [
    "Ali Khaledi Nasab",
    "TechCorp Inc connections to government contracts",
    "Recent cybersecurity incidents in financial sector",
    "Dr. Sarah Johnson research collaborations",
  ];

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold mb-4">Start New Investigation</h2>
        <p className="text-gray-400">
          Enter your OSINT query to begin multi-agent intelligence gathering
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Query Input */}
        <div className="bg-gray-900 rounded-lg p-6">
          <label className="block text-sm font-medium mb-2">Investigation Query</label>
          <div className="relative">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter person name, organization, or topic to investigate..."
              className="w-full h-32 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg 
                       text-white placeholder-gray-500 focus:border-cyan-500 focus:ring-1 
                       focus:ring-cyan-500 resize-none"
              disabled={isLoading}
            />
          </div>
        </div>

        {/* Focus Areas */}
        <div className="bg-gray-900 rounded-lg p-6">
          <label className="block text-sm font-medium mb-4">Focus Areas</label>
          <div className="grid grid-cols-2 gap-3">
            {focusAreaOptions.map((area) => {
              const Icon = area.icon;
              const isSelected = settings.focusAreas.includes(area.id);
              return (
                <button
                  key={area.id}
                  type="button"
                  onClick={() => toggleFocusArea(area.id)}
                  className={`flex items-center space-x-2 px-4 py-3 rounded-lg border-2 
                            transition-all ${
                    isSelected
                      ? "border-cyan-500 bg-cyan-500/10 text-cyan-500"
                      : "border-gray-700 hover:border-gray-600 text-gray-400"
                  }`}
                  disabled={isLoading}
                >
                  <Icon className="w-4 h-4" />
                  <span>{area.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Entity Types */}
        <div className="bg-gray-900 rounded-lg p-6">
          <label className="block text-sm font-medium mb-4">Expected Entity Types</label>
          <div className="flex flex-wrap gap-2">
            {entityTypeOptions.map((type) => {
              const isSelected = settings.entityTypes.includes(type.id);
              return (
                <button
                  key={type.id}
                  type="button"
                  onClick={() => toggleEntityType(type.id)}
                  className={`px-4 py-2 rounded-full text-sm transition-all ${
                    isSelected
                      ? "bg-cyan-500 text-white"
                      : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}
                  disabled={isLoading}
                >
                  {type.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Retrieval Settings */}
        <div className="bg-gray-900 rounded-lg p-6">
          <label className="block text-sm font-medium mb-2">
            Maximum Retrievals: {settings.maxRetrievals}
          </label>
          <input
            type="range"
            min="8"
            max="20"
            value={settings.maxRetrievals}
            onChange={(e) => setSettings({ ...settings, maxRetrievals: parseInt(e.target.value) })}
            className="w-full"
            disabled={isLoading}
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Basic (8)</span>
            <span>Standard (12)</span>
            <span>Comprehensive (20)</span>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="w-full bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-700 
                   disabled:cursor-not-allowed text-white font-medium py-3 px-6 
                   rounded-lg transition-colors flex items-center justify-center space-x-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Investigating...</span>
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              <span>Start Investigation</span>
            </>
          )}
        </button>
      </form>

      {/* Example Queries */}
      <div className="mt-8">
        <p className="text-sm text-gray-500 mb-3">Example queries:</p>
        <div className="flex flex-wrap gap-2">
          {exampleQueries.map((example, idx) => (
            <button
              key={idx}
              onClick={() => setQuery(example)}
              className="px-3 py-1 bg-gray-800 hover:bg-gray-700 text-gray-400 
                       text-sm rounded-full transition-colors"
              disabled={isLoading}
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}; 