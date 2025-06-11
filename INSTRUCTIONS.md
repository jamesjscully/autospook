Technical Interview: OSINT AI Agent 
Problem Statement
Design and implement an OSINT (Open Source Intelligence) AI agent that processes intelligence queries through automated multi-source data retrieval and generates comprehensive investigative reports. The system must perform strategic information gathering across multiple open sources and synthesize findings into actionable intelligence.
System Requirements
Core OSINT Workflow
Your system must implement the following agent-based OSINT pipeline:
Query Analysis Agent: Parse customer requests for OSINT on specific entities (persons, organizations, locations, events)
Simple stepback prompting


OSINT Planning & Orchestration Agent:


Decompose queries into strategic OSINT collection tasks
Plan multi-source retrieval strategies across different data types
Coordinate between retrieval, analysis, and pivot agents
Prioritize sources based on reliability and relevance
Multi-Source Retrieval & Analysis Agent Collaboration:


Retrieval Agent: Execute searches across multiple OSINT sources:
Web search for news articles, press releases, public documents
Social media analysis (LinkedIn, Twitter/X, public profiles)
Academic and research publications
Government databases and public records
Company registrations and business intelligence
Pivot Agent: Analyze retrieved data to: https://github.com/google-gemini/gemini-fullstack-langgraph-quickstart


Identify new investigation angles and related entities
Cross-reference information across sources
Detect inconsistencies and information gaps
Generate follow-up search strategies
Minimum Requirement: Must perform at least 8-12 distinct retrievals per investigation


Synthesis & Reporting Agent:


Aggregate OSINT findings into coherent intelligence narratives
Generate structured reports with source attribution and confidence scores
Handle large context windows (process 3M+ tokens of collected OSINT data)
Provide risk assessment and threat indicators
Technical Constraints
Framework: Must use LangGraph for agent orchestration with persistent memory architecture
Reference Implementation: You can use this repository as your foundation:
Frontend: Must implement React-based user interface for agent interaction and report visualization
Models: Implement with at least 3 different LLM models:
Fast retrieval model: Claude Sonnet 4 for query parsing and search orchestration
Analysis model: GPT-4o for cross-reference analysis and pivot generation
Synthesis model: Gemini 1.5 Pro for final report generation with large context
System Prompts: Must develop elaborate, detailed system prompts for each agent that clearly define their roles, capabilities, and interaction patterns
Memory Requirements: Your LangGraph implementation must include robust memory systems that persist across agent interactions and maintain state
OSINT Memory System: Agents must maintain persistent memory of:
Source reliability and credibility scores
Entity relationship mapping and network analysis
Temporal intelligence and timeline construction
Evidence correlation and cross-validation
Context Management: System must handle scenarios where OSINT data exceeds context limits

Implementation Architecture
LangGraph Requirements
Your LangGraph implementation must include:
Proper state management across all agent interactions
Persistent memory that maintains context between agent calls
Dynamic routing based on information quality and completeness
Error handling and recovery for failed retrievals
State persistence that survives system restarts
Agent System Prompts
Each agent requires elaborate, comprehensive system prompts that define:
Specific role and responsibilities within the OSINT pipeline
Interaction protocols with other agents
Decision-making criteria and escalation procedures
Output formatting and quality standards
Memory utilization and state management protocols
Model Specialization
Claude Sonnet 4: Query parsing, search strategy, and source prioritization
GPT-4o: Cross-referencing, fact verification, and analytical reasoning
Gemini 1.5 Pro: Large context synthesis, timeline construction, and final reporting
Claude Opus 4: LLM as a judge using Claude 4 Opus before reporting the final results. 
OSINT Memory Architecture
Source credibility tracking with time-decay scoring
Entity relationship graphs with confidence weighting
Information provenance and chain-of-custody tracking
Automated duplicate detection and information clustering
Evaluation Criteria
OSINT Effectiveness
Minimum 8-12 successful retrievals per investigation
Source diversity and comprehensive coverage
Information quality and relevance scoring
Cross-source validation and fact-checking
Agent Coordination
Effective LangGraph implementation with proper OSINT state management
Strategic retrieval sequencing and pivot decisions
Memory persistence and source attribution
Technical Implementation
Integration with the provided GitHub repository architecture
Effective use of 3+ models with clear role separation
Robust error handling for failed retrievals
Scalable context management
Intelligence Quality
Report coherence and analytical depth
Risk assessment accuracy and threat identification
Source attribution and confidence scoring
Handling of contradictory information
Required Test Case & Report Generation
Primary Investigation Target: Your OSINT agent must successfully generate a comprehensive intelligence report on: Ali Khaledi Nasab
Investigation Requirements:
Conduct systematic OSINT investigation across multiple sources
Gather intelligence on professional background, business associations, public activities
Identify potential risk indicators and network connections
Cross-reference findings for accuracy and completeness
Generate clean, professional intelligence report with proper source attribution
Expected Agent Behavior:
Perform 10+ strategic retrievals across diverse OSINT sources
Cross-reference findings to build comprehensive profile
Identify network connections and business relationships
Generate risk assessment with evidence-based scoring
Produce clean, professional intelligence report suitable for executive briefing
Success Criteria:
Minimum 8 distinct, successful information retrievals
Evidence of cross-source validation and fact-checking
Professional-grade report with clear source attribution and confidence scores
Demonstration of analytical reasoning and risk assessment capabilities
React frontend that clearly displays the investigation process and final report
Deliverables
Complete Codebase:


LangGraph OSINT implementation with persistent memory
React-based frontend for agent interaction and report visualization
Elaborate system prompts for each agent with detailed role definitions
Integration with the provided GitHub repository architecture
Live Demonstration: 45-minute presentation showing:


Multi-source OSINT collection process in real-time
Agent memory persistence and state management
Cross-source analysis and validation workflow
Generation of comprehensive intelligence report on Ali Khaledi Nasab
React frontend functionality and user experience
Documentation:


Architecture overview and agent interaction flows
System prompt documentation and design rationale
Deployment and setup instructions
Time Allocation: 36 hours for implementation + 75 minutes presentation
Bonus Points
Implementation of automated source credibility scoring
Network analysis and relationship mapping visualization
Timeline construction from temporal intelligence
Risk scoring algorithms based on collected intelligence
Integration with additional specialized OSINT tools
This challenge evaluates your ability to build production-ready OSINT agents that can systematically gather, analyze, and synthesize open source intelligence through automated multi-source collection strategies.
