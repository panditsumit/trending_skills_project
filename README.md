# trending_skills_project

A job market analyst that surfaces the AI skills worth learning in 2026—using live web search, not hype.

It runs an agent that calls MCP tools to gather real-time demand data, then synthesizes the findings into a prioritized skill report with a specific action plan.

```
┌─────────────────────────────────────────────────────────────┐
│                        Agent Agent                         │
│  ┌─────────────┐  ┌───────────┐  ┌───────────────────┐     │
│  │   Tool Call │─▶│   Tools   │◀─│  Synthesize       │     │
│  │  (MCP)      │  │ (FastMCP) │  │  JSON Report      │     │
│  └─────────────┘  └───────────┘  └───────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Stack

- **FastMCP** - Server for MCP tools (Tavily search)
- **LangGraph** - Agent state machine
- **Ollama GLM-5.1** - LLM for tool calling and report synthesis
- **Tavily** - Live web search for job market data

## Setup

```bash
git clone https://github.com/sumitpandit/trending_skills_project.git
cd trending_skills_project
pip install -r requirements.txt
cp .env.example .env  # add your TAVILY_API_KEY
python agent.py
```

## Sample Output

```
============================================================
   AI Skill Roadmap - 
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

🔥 Top Skills to Learn Now
 1. Agentic AI / AI Agents - Demand surged up to 60x YoY
 2. MLOps / LLMOps - Enterprise adoption accelerating
 3. RAG (Retrieval-Augmented Generation) - 143% posting growth

📈 Fastest Growing
 Agentic AI, AI Engineer, LangChain

⚠️Losing Ground
 Generic AI credentials, Pure model-building without deployment

💡Action Plan
 Week 1-2: Build a RAG pipeline with LangChain
 Week 3-4: Implement an MCP server wrapping an existing API
 Week 5-6: Combine both into a LangChain agent

🔗MCP Insight 
 MCP has hit 97M installs—crossed from experimental to industry standard.

📊 Live - Tavily web search | April 2026
============================================================
```

[View demo video (LinkedIn)](https://www.linkedin.com/...) <!-- update after posting -->
