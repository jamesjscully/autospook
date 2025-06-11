import React, { useState } from "react";
import { useInvestigation } from "@/contexts/InvestigationContext";
import { Download, Copy, CheckCircle, FileText, Shield, AlertTriangle } from "lucide-react";

export const ReportViewer: React.FC = () => {
  const { investigation } = useInvestigation();
  const [copied, setCopied] = useState(false);

  if (!investigation || !investigation.report) {
    return (
      <div className="text-center py-12">
        <FileText className="w-12 h-12 text-gray-600 mx-auto mb-4" />
        <p className="text-gray-500">No report available yet</p>
      </div>
    );
  }

  const report = investigation.report;

  const handleCopy = () => {
    const reportText = JSON.stringify(report, null, 2);
    navigator.clipboard.writeText(reportText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const reportText = JSON.stringify(report, null, 2);
    const blob = new Blob([reportText], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `osint_report_${investigation.id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case "high":
        return "text-red-500 bg-red-500/10";
      case "medium":
        return "text-yellow-500 bg-yellow-500/10";
      case "low":
        return "text-green-500 bg-green-500/10";
      default:
        return "text-gray-500 bg-gray-500/10";
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold mb-2">Intelligence Report</h2>
          <p className="text-gray-400">Investigation ID: {investigation.id}</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 
                     rounded-lg transition-colors"
          >
            {copied ? (
              <>
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-sm">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                <span className="text-sm">Copy</span>
              </>
            )}
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center space-x-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 
                     rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            <span className="text-sm">Download</span>
          </button>
        </div>
      </div>

      {/* Executive Summary */}
      {report.executive_summary && (
        <div className="bg-gray-900 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Shield className="w-5 h-5 mr-2 text-cyan-500" />
            Executive Summary
          </h3>
          <p className="text-gray-300 leading-relaxed">{report.executive_summary}</p>
        </div>
      )}

      {/* Key Findings */}
      {report.key_findings && report.key_findings.length > 0 && (
        <div className="bg-gray-900 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Key Findings</h3>
          <ul className="space-y-3">
            {report.key_findings.map((finding: any, idx: number) => (
              <li key={idx} className="flex items-start">
                <div className="w-2 h-2 bg-cyan-500 rounded-full mt-2 mr-3 flex-shrink-0" />
                <div>
                  <p className="text-gray-300">{finding.finding || finding}</p>
                  {finding.confidence && (
                    <span className="text-xs text-gray-500 mt-1">
                      Confidence: {finding.confidence}%
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Entity Analysis */}
      {report.entities && report.entities.length > 0 && (
        <div className="bg-gray-900 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Identified Entities</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.entities.map((entity: any, idx: number) => (
              <div key={idx} className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">{entity.name}</h4>
                  <span className="text-xs px-2 py-1 bg-gray-700 rounded-full">
                    {entity.type}
                  </span>
                </div>
                {entity.description && (
                  <p className="text-sm text-gray-400">{entity.description}</p>
                )}
                {entity.confidence && (
                  <div className="mt-2">
                    <div className="flex items-center justify-between text-xs">
                      <span>Confidence</span>
                      <span>{entity.confidence}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-1 mt-1">
                      <div
                        className="bg-cyan-500 h-1 rounded-full"
                        style={{ width: `${entity.confidence}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Assessment */}
      {report.risk_assessment && (
        <div className="bg-gray-900 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2 text-yellow-500" />
            Risk Assessment
          </h3>
          <div className="space-y-4">
            {report.risk_assessment.overall_risk && (
              <div className="flex items-center justify-between">
                <span className="font-medium">Overall Risk Level</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  getRiskColor(report.risk_assessment.overall_risk)
                }`}>
                  {report.risk_assessment.overall_risk.toUpperCase()}
                </span>
              </div>
            )}
            {report.risk_assessment.factors && (
              <div>
                <p className="text-sm text-gray-400 mb-2">Risk Factors:</p>
                <ul className="space-y-1">
                  {report.risk_assessment.factors.map((factor: string, idx: number) => (
                    <li key={idx} className="text-sm text-gray-300 flex items-start">
                      <span className="mr-2">•</span>
                      {factor}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sources */}
      {report.sources && report.sources.length > 0 && (
        <div className="bg-gray-900 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Sources ({report.sources.length})</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {report.sources.map((source: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <span className="text-gray-400 truncate">
                  {source.title || source.url || `Source ${idx + 1}`}
                </span>
                {source.credibility && (
                  <span className="text-xs text-gray-500">
                    Credibility: {source.credibility}/10
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quality Score */}
      {report.quality_score && (
        <div className="bg-gray-900 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Report Quality Assessment</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span>Overall Quality</span>
              <span className="text-2xl font-bold text-cyan-500">
                {report.quality_score.overall}%
              </span>
            </div>
            {report.quality_score.breakdown && (
              <div className="space-y-2">
                {Object.entries(report.quality_score.breakdown).map(([key, value]: [string, any]) => (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <span className="text-gray-400 capitalize">
                      {key.replace(/_/g, " ")}
                    </span>
                    <span>{value}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}; 