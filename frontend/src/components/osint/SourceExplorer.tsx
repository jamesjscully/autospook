import React, { useState } from "react";
import { useInvestigation } from "@/contexts/InvestigationContext";
import { ExternalLink, Filter, Database, Calendar, Tag } from "lucide-react";

export const SourceExplorer: React.FC = () => {
  const { investigation } = useInvestigation();
  const [filter, setFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");

  if (!investigation || investigation.sources.length === 0) {
    return (
      <div className="text-center py-12">
        <Database className="w-12 h-12 text-gray-600 mx-auto mb-4" />
        <p className="text-gray-500">No sources gathered yet</p>
      </div>
    );
  }

  const sourceTypes = [
    { id: "all", label: "All Sources" },
    { id: "web", label: "Web" },
    { id: "social", label: "Social Media" },
    { id: "records", label: "Public Records" },
    { id: "academic", label: "Academic" },
    { id: "news", label: "News" },
  ];

  const filteredSources = investigation.sources.filter((source: any) => {
    const matchesFilter = filter === "all" || source.type === filter;
    const matchesSearch = searchTerm === "" || 
      source.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      source.content?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getSourceIcon = (type: string) => {
    switch (type) {
      case "social":
        return "🌐";
      case "records":
        return "📋";
      case "academic":
        return "🎓";
      case "news":
        return "📰";
      default:
        return "🔍";
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2">Source Explorer</h2>
        <p className="text-gray-400">
          {investigation.sources.length} sources gathered • {filteredSources.length} shown
        </p>
      </div>

      {/* Filters and Search */}
      <div className="bg-gray-900 rounded-lg p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search sources..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg
                       text-white placeholder-gray-500 focus:border-cyan-500"
            />
          </div>
          
          {/* Type Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg
                       text-white focus:border-cyan-500"
            >
              {sourceTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Sources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredSources.map((source: any, idx: number) => (
          <div key={idx} className="bg-gray-900 rounded-lg p-6 hover:bg-gray-800 transition-colors">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">{getSourceIcon(source.type)}</span>
                <div>
                  <h3 className="font-medium line-clamp-1">
                    {source.title || "Untitled Source"}
                  </h3>
                  <p className="text-xs text-gray-500">{source.type || "Unknown"}</p>
                </div>
              </div>
              {source.url && (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-cyan-500 hover:text-cyan-400"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}
            </div>

            {/* Source Content Preview */}
            {source.content && (
              <p className="text-sm text-gray-400 line-clamp-3 mb-3">
                {source.content}
              </p>
            )}

            {/* Metadata */}
            <div className="flex flex-wrap gap-2 text-xs">
              {source.date && (
                <div className="flex items-center space-x-1 text-gray-500">
                  <Calendar className="w-3 h-3" />
                  <span>{new Date(source.date).toLocaleDateString()}</span>
                </div>
              )}
              {source.credibility && (
                <div className="flex items-center space-x-1 text-gray-500">
                  <span>Credibility: {source.credibility}/10</span>
                </div>
              )}
              {source.tags && source.tags.length > 0 && (
                <div className="flex items-center space-x-1">
                  <Tag className="w-3 h-3 text-gray-500" />
                  {source.tags.slice(0, 3).map((tag: string, tagIdx: number) => (
                    <span key={tagIdx} className="px-2 py-1 bg-gray-800 rounded-full text-gray-400">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Related Entities */}
            {source.entities && source.entities.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-800">
                <p className="text-xs text-gray-500 mb-1">Related Entities:</p>
                <div className="flex flex-wrap gap-1">
                  {source.entities.map((entity: any, entityIdx: number) => (
                    <span
                      key={entityIdx}
                      className="text-xs px-2 py-1 bg-cyan-500/10 text-cyan-500 rounded"
                    >
                      {entity.name || entity}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredSources.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No sources match your filters</p>
        </div>
      )}
    </div>
  );
}; 