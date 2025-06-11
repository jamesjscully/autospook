import React from "react";
import { useInvestigation } from "@/contexts/InvestigationContext";
import { Network, User, Building, MapPin, Calendar } from "lucide-react";

export const EntityGraph: React.FC = () => {
  const { investigation } = useInvestigation();

  if (!investigation || investigation.entities.length === 0) {
    return (
      <div className="text-center py-12">
        <Network className="w-12 h-12 text-gray-600 mx-auto mb-4" />
        <p className="text-gray-500">No entities identified yet</p>
      </div>
    );
  }

  const getEntityIcon = (type: string) => {
    switch (type) {
      case "person":
        return User;
      case "organization":
        return Building;
      case "location":
        return MapPin;
      case "event":
        return Calendar;
      default:
        return Network;
    }
  };

  const getEntityColor = (type: string) => {
    switch (type) {
      case "person":
        return "bg-blue-500/10 text-blue-500 border-blue-500/20";
      case "organization":
        return "bg-green-500/10 text-green-500 border-green-500/20";
      case "location":
        return "bg-yellow-500/10 text-yellow-500 border-yellow-500/20";
      case "event":
        return "bg-purple-500/10 text-purple-500 border-purple-500/20";
      default:
        return "bg-gray-500/10 text-gray-500 border-gray-500/20";
    }
  };

  // Group entities by type
  const groupedEntities = investigation.entities.reduce((acc: any, entity: any) => {
    const type = entity.type || "unknown";
    if (!acc[type]) acc[type] = [];
    acc[type].push(entity);
    return acc;
  }, {});

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2">Entity Graph</h2>
        <p className="text-gray-400">
          {investigation.entities.length} entities identified across {Object.keys(groupedEntities).length} categories
        </p>
      </div>

      {/* Entity Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {Object.entries(groupedEntities).map(([type, entities]: [string, any]) => {
          const Icon = getEntityIcon(type);
          return (
            <div key={type} className="bg-gray-900 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <Icon className="w-5 h-5 text-gray-400" />
                <span className="text-2xl font-bold">{entities.length}</span>
              </div>
              <p className="text-sm text-gray-400 capitalize">{type}s</p>
            </div>
          );
        })}
      </div>

      {/* Entity Cards */}
      <div className="space-y-6">
        {Object.entries(groupedEntities).map(([type, entities]: [string, any]) => {
          const Icon = getEntityIcon(type);
          const colorClass = getEntityColor(type);
          
          return (
            <div key={type} className="bg-gray-900 rounded-lg p-6">
              <h3 className="flex items-center space-x-2 text-lg font-semibold mb-4">
                <Icon className="w-5 h-5" />
                <span className="capitalize">{type} Entities</span>
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {entities.map((entity: any, idx: number) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-lg border-2 ${colorClass}`}
                  >
                    <h4 className="font-medium mb-2">{entity.name}</h4>
                    
                    {/* Attributes */}
                    {entity.attributes && Object.keys(entity.attributes).length > 0 && (
                      <div className="space-y-1 mb-3">
                        {Object.entries(entity.attributes).slice(0, 3).map(([key, value]: [string, any]) => (
                          <div key={key} className="text-xs">
                            <span className="text-gray-500">{key}:</span>{" "}
                            <span className="text-gray-300">{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* Confidence */}
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">Confidence</span>
                      <span>{entity.confidence}%</span>
                    </div>
                    <div className="w-full bg-gray-800 rounded-full h-1 mt-1">
                      <div
                        className="bg-current h-1 rounded-full"
                        style={{ width: `${entity.confidence}%` }}
                      />
                    </div>
                    
                    {/* Source Count */}
                    {entity.sources && (
                      <p className="text-xs text-gray-500 mt-2">
                        Found in {entity.sources.length} source{entity.sources.length !== 1 ? 's' : ''}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Placeholder for Future Graph Visualization */}
      <div className="mt-8 bg-gray-900 rounded-lg p-12 text-center">
        <Network className="w-16 h-16 text-gray-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Interactive Graph Visualization</h3>
        <p className="text-gray-400 max-w-2xl mx-auto">
          Future enhancement: Interactive force-directed graph showing entity relationships,
          connections, and data flow between identified entities.
        </p>
      </div>
    </div>
  );
}; 