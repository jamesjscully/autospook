# AutoSpook - OSINT AI Agent System

An intelligent Open Source Intelligence (OSINT) gathering system that leverages multi-agent architecture with LangGraph orchestration to perform comprehensive investigations and generate actionable intelligence reports.

Based on the Gemini Fullstack LangGraph Quickstart, this system extends the research capabilities to focus on OSINT operations with specialized agents for query analysis, multi-source retrieval, pivot analysis, and professional report generation.

![Gemini Fullstack LangGraph](./app.png)

## Features

- 🕵️ Multi-agent OSINT architecture with specialized intelligence gathering agents
- 🧠 6 specialized agents: Query Analysis, Orchestration, Retrieval, Pivot Analysis, Synthesis, and Quality Judge
- 🔍 Multi-source intelligence gathering (web, social media, public records, academic sources)
- 🌐 Minimum 8-12 strategic retrievals per investigation across diverse sources
- 💾 Persistent memory system with entity graphs and source credibility tracking
- 📊 Professional intelligence reports with risk assessment and confidence scoring
- 🎯 Specialized for investigating persons, organizations, locations, and events
- 🔄 Iterative investigation with intelligent pivoting and follow-up strategies

## Project Structure

The project is divided into two main directories:

-   `frontend/`: Contains the React application built with Vite.
-   `backend/`: Contains the LangGraph/FastAPI application, including the research agent logic.

## Getting Started: Development and Local Testing

Follow these steps to get the application running locally for development and testing.

**1. Prerequisites:**

-   Node.js 18+ and npm (or yarn/pnpm)
-   Python 3.10+
-   PostgreSQL 15+
-   Redis 7+
-   **Required API Keys:**
    - `GEMINI_API_KEY`: Google Gemini API key (for Gemini 1.5 Pro)
    - `ANTHROPIC_API_KEY`: Anthropic API key (for Claude Sonnet 4 & Opus 4)
    - `OPENAI_API_KEY`: OpenAI API key (for GPT-4o)
    - `GOOGLE_SEARCH_API_KEY` & `GOOGLE_CSE_ID`: For web search capabilities
    - `LANGSMITH_API_KEY`: For monitoring and debugging
    
    1.  Navigate to the `backend/` directory.
    2.  Create a file named `.env` by copying the `backend/.env.example` file.
    3.  Add all your API keys to the `.env` file

**2. Install Dependencies:**

**Backend:**

```bash
cd backend
pip install .
```

**Frontend:**

```bash
cd frontend
npm install
```

**3. Run Development Servers:**

**Backend & Frontend:**

```bash
make dev
```
This will run the backend and frontend development servers.    Open your browser and navigate to the frontend development server URL (e.g., `http://localhost:5173/app`).

_Alternatively, you can run the backend and frontend development servers separately. For the backend, open a terminal in the `backend/` directory and run `langgraph dev`. The backend API will be available at `http://127.0.0.1:2024`. It will also open a browser window to the LangGraph UI. For the frontend, open a terminal in the `frontend/` directory and run `npm run dev`. The frontend will be available at `http://localhost:5173`._

## How the OSINT Agent System Works

The AutoSpook system implements a sophisticated multi-agent OSINT pipeline:

![Agent Flow](./agent.png)

1.  **Query Analysis (Claude Sonnet 4):** Parses OSINT requests, extracts entities (persons, organizations, locations), and applies stepback prompting for query refinement.

2.  **Planning & Orchestration (Claude Sonnet 4):** Decomposes queries into strategic collection tasks, prioritizes sources, and coordinates parallel retrieval operations.

3.  **Multi-Source Retrieval (Claude Sonnet 4):** Executes 8-12+ searches across diverse sources including web, social media, public records, and academic databases.

4.  **Pivot Analysis (GPT-4o):** Analyzes retrieved data to identify new investigation angles, cross-references information, and generates follow-up strategies.

5.  **Synthesis & Reporting (Gemini 1.5 Pro):** Processes 3M+ tokens of collected OSINT data to generate comprehensive intelligence reports with source attribution.

6.  **Quality Assurance (Claude Opus 4):** Acts as final judge to verify report accuracy, completeness, and professional standards before delivery.

## Deployment

In production, the backend server serves the optimized static frontend build. LangGraph requires a Redis instance and a Postgres database. Redis is used as a pub-sub broker to enable streaming real time output from background runs. Postgres is used to store assistants, threads, runs, persist thread state and long term memory, and to manage the state of the background task queue with 'exactly once' semantics. For more details on how to deploy the backend server, take a look at the [LangGraph Documentation](https://langchain-ai.github.io/langgraph/concepts/deployment_options/). Below is an example of how to build a Docker image that includes the optimized frontend build and the backend server and run it via `docker-compose`.

_Note: For the docker-compose.yml example you need a LangSmith API key, you can get one from [LangSmith](https://smith.langchain.com/settings)._

_Note: If you are not running the docker-compose.yml example or exposing the backend server to the public internet, you update the `apiUrl` in the `frontend/src/App.tsx` file your host. Currently the `apiUrl` is set to `http://localhost:8123` for docker-compose or `http://localhost:2024` for development._

**1. Build the Docker Image:**

   Run the following command from the **project root directory**:
   ```bash
   docker build -t gemini-fullstack-langgraph -f Dockerfile .
   ```
**2. Run the Production Server:**

   ```bash
   GEMINI_API_KEY=<your_gemini_api_key> LANGSMITH_API_KEY=<your_langsmith_api_key> docker-compose up
   ```

Open your browser and navigate to `http://localhost:8123/app/` to see the application. The API will be available at `http://localhost:8123`.

## Technologies Used

- [React](https://reactjs.org/) (with [Vite](https://vitejs.dev/)) - For the frontend user interface.
- [Tailwind CSS](https://tailwindcss.com/) - For styling.
- [Shadcn UI](https://ui.shadcn.com/) - For components.
- [LangGraph](https://github.com/langchain-ai/langgraph) - For building the backend research agent.
- [Google Gemini](https://ai.google.dev/models/gemini) - LLM for query generation, reflection, and answer synthesis.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
