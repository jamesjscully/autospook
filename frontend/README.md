# AutoSpook OSINT Frontend

A modern React-based user interface for the AutoSpook OSINT (Open Source Intelligence) multi-agent system.

## Features

- **Multi-Tab Interface**: Organized workflow with tabs for Query, Progress, Entity Graph, Sources, and Report viewing
- **Real-time Progress Tracking**: Live updates showing each agent's status and progress
- **Entity Visualization**: View and explore identified entities (persons, organizations, locations, events)
- **Source Explorer**: Browse, filter, and search through gathered intelligence sources
- **Professional Reports**: View and export comprehensive OSINT investigation reports
- **Dark Theme UI**: Optimized for extended investigation sessions

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── osint/
│   │       ├── OSINTDashboard.tsx    # Main dashboard with tab navigation
│   │       ├── QueryInterface.tsx     # Investigation query form
│   │       ├── InvestigationProgress.tsx  # Real-time agent status
│   │       ├── EntityGraph.tsx        # Entity visualization
│   │       ├── SourceExplorer.tsx     # Source browsing interface
│   │       └── ReportViewer.tsx       # Final report display
│   ├── contexts/
│   │   └── InvestigationContext.tsx   # Global investigation state
│   ├── OSINTApp.tsx                   # Main OSINT application wrapper
│   └── App.tsx                        # Entry point
└── package.json
```

## Setup Instructions

### Prerequisites

- Node.js 18+ and npm (or yarn/pnpm)
- Backend server running on http://localhost:2024 (development) or http://localhost:8123 (production)

### Installation

1. Install Node.js and npm if not already installed:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install nodejs npm

   # Or use NodeSource repository for latest version
   curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

2. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open http://localhost:5173 in your browser

## Key Components

### QueryInterface
- Investigation query input with entity type and source focus area selection
- Configurable retrieval count (8-20 retrievals)
- Example queries for quick testing

### InvestigationProgress
- Real-time status of all 6 OSINT agents
- Progress bars for overall and per-agent progress
- Live activity feed showing sources being gathered

### EntityGraph
- Grouped display of identified entities by type
- Confidence scores and source counts
- Future: Interactive force-directed graph visualization

### SourceExplorer
- Filter sources by type (web, social, records, academic, news)
- Search through source titles and content
- View metadata including credibility scores and related entities

### ReportViewer
- Executive summary and key findings
- Entity analysis with confidence scores
- Risk assessment with factors
- Source citations with credibility ratings
- Export options (copy/download JSON)

## Technology Stack

- **React 19** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **LangGraph SDK** for backend communication
- **Radix UI** for accessible components

## Backend Integration

The frontend communicates with the OSINT backend through the LangGraph SDK. Key events handled:

- `query_analysis`: Entity extraction results
- `retrieval_progress`: Real-time source gathering updates
- `pivot_analysis`: New investigation angles discovered
- `report_generation`: Final report data
- `quality_assessment`: Report quality metrics

## Development

### Running Tests
```bash
npm test
```

### Building for Production
```bash
npm run build
```

### Linting
```bash
npm run lint
```

## Future Enhancements

1. **Interactive Entity Graph**: D3.js force-directed graph showing entity relationships
2. **Timeline View**: Chronological display of events and activities
3. **Collaborative Features**: Share investigations and collaborate in real-time
4. **Advanced Filtering**: Complex queries across sources and entities
5. **Export Formats**: PDF reports, CSV data exports
6. **Dark/Light Theme Toggle**: User preference persistence
7. **Mobile Responsive Design**: Optimized layouts for tablets and phones

## Contributing

Please follow the existing code style and component patterns. All new components should:
- Use TypeScript with proper type definitions
- Follow the established color scheme (cyan accents on dark gray)
- Include loading and error states
- Be accessible (ARIA labels, keyboard navigation) 