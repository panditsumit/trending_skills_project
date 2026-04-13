"""
FastMCP Server: Job Market Analyzer
Tools: get_trending_skills, get_job_demand, compare_skills
Data: Live - powered by Tavily Search API
"""

import os
from fastmcp import FastMCP
from tavily import TavilyClient
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

mcp = FastMCP("Job Market Analyzer")
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# Shared Tavily search helper

def tavily_search(query: str, max_results: int = 5) -> dict:
    """Run a Tavily search and return a clean result dict."""
    response = tavily.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        include_answer=True,
    )

    return {
        "answer": response.get("answer", ""),
        "results": [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:600], # trim for token efficiency
            }
            for r in response.get("results", [])
        ]
    }

# MCP Tools

@mcp.tool()
def get_trending_skills(role: str) -> dict:
    """
    Searches the web for the most in-demand AI skills for a given job role in 2026.

    Args: 
        role: Job role/title e.g. "Java Developer", "ML Engineer", "Data Engineer"

    Returns:
        Live search results with trending skills, sources, and a summary answer

    """
    query = f"most in-demand AI skills for {role} 2026 hiring trends job market"
    data = tavily_search(query, max_results=5)

    return {
        "role": role,
        "query_used": query,
        "summary": data["answer"],
        "sources": data["results"],
        "data_source": "Live - Tavily web search"
    }

@mcp.tool()
def get_job_demand(skill: str) -> dict:
    """
    Searches the web for current hiring demand, growth trend, and market signal
    for a specific AI/tech skill.

    Args: 
        skill: Skill name e.g. 'MCP', 'LangGraph', 'RAG', 'Agentic AI'

    Returns:
        Live demand analysis with sources
    """
    query = f"{skill} skill demand job market hiring trend 2026"
    data = tavily_search(query, max_results=4)

    return {
        "skill": skill,
        "query_used": query,
        "market_summary": data["answer"],
        "sources": data["results"],
        "data_sources": "Live - Tavily web search"
    }

@mcp.tool 
def compare_skills(skill1: str, skill2: str) -> dict:
    """
    Searches the web to compare two skills by job market demand and career value in 2026.

    Args: 
        skill1: First skill e.g. 'MCP'
        skill2: Second skill e.g. 'LangChain'

    Returns:
        Live comparison with sources and a summary
    """
    query = f"{skill1} vs {skill2} AI jobs career demand comparison 2026"
    data = tavily_search(query, max_results=5)

    return {
        "skill1": skill1,
        "skill2": skill2,
        "query_used": query,
        "comparison_summary": data["answer"],
        "sources": data["results"],
        "data_source": "Live - Tavily web search"
    }

if __name__ == "__main__":
    mcp.run()
