import { useState, useCallback } from "react";
import { OSINTDashboard } from "@/components/osint/OSINTDashboard";
import { InvestigationProvider } from "@/contexts/InvestigationContext";

export default function OSINTApp() {
  return (
    <InvestigationProvider>
      <div className="min-h-screen bg-gray-950 text-gray-100">
        <OSINTDashboard />
      </div>
    </InvestigationProvider>
  );
} 