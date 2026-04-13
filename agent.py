"""
Langgraph Agent: Job Marked Analyzer
LLM: Ollama (glm-5.1:cloud)
Output: Pydantic strcutured report
MCP: FastMCP server via stdio
"""

import asyncio
import re
from typing import Annotated, TypedDict

from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

# Pydantic Structured Output Schema


class SkillEntry(BaseModel):
    # Support both 'name' and 'skill' as field name
    name: str = Field(default="", description="Skill name")
    skill: str = Field(default="", description="Alternative skill name")
    why: str = Field(default="", description="One-linee reason skill matters now")

    def model_post_init(self, __context):
        # If 'skill' is populated but 'name' is empty, use 'skill' as 'name'
        if self.skill and not self.name:
            self.name = self.skill


class SkillReport(BaseModel):
    role: str = Field(default="", description="The job role analyzed")
    top_skills: list[SkillEntry] = Field(default_factory=list, description="Top 3 skills to learn now, ranked by demand")
    fastest_growing: str | list = Field(default="", description="Skills losing market relevance")
    declining_skills: list[str] | list[dict] = Field(default_factory=list, description="Skills losing market relevance")
    action_plan: str | list = Field(default="", description="2-3 sharp, specific sentences. No Filler")
    mcp_insight: str = Field(default="", description="One specific insight about MCP's role in the job market right now")
    data_source: str = Field(default="Live - Tavily web search | April 2026", description="Data source")

    def model_post_init(self, __context):
        # Convert lists to strings where needed
        if isinstance(self.fastest_growing, list):
            self.fastest_growing = ", ".join(str(s) for s in self.fastest_growing)
        if isinstance(self.declining_skills, list) and self.declining_skills and isinstance(self.declining_skills[0], dict):
            self.declining_skills = [d.get('skill', str(d)) for d in self.declining_skills]
        if isinstance(self.action_plan, list):
            self.action_plan = " ".join(str(p) for p in self.action_plan)


# State


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    final_report: SkillReport | None


# LLM
llm = ChatOllama(model="glm-5.1:cloud", temperature=0)


# Custom parser to extract JSON from markdown-wrapped responses
class MarkdownJsonOutputParser:
    """Parse LLM output to SkillReport, handling markdown-wrapped JSON."""

    def parse(self, text: str) -> SkillReport:
        """Parse text containing potentially markdown-wrapped JSON."""
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        else:
            # Try to find JSON object starting with {
            json_start = text.find('{')
            if json_start != -1:
                text = text[json_start:]
            else:
                raise ValueError("No JSON found in response")

        # Clean up the text
        text = text.strip()

        # Use pydantic to parse the JSON
        return SkillReport.model_validate_json(text)


llm_structured = llm.with_structured_output(SkillReport)


# Build graph
async def build_agent():
    client = MultiServerMCPClient(
        {
            "job_market": {
                "command": "python",
                "args": ["server.py"],
                "transport": "stdio",
            }
        }
    )

    tools = await client.get_tools()
    llm_with_tools = llm.bind_tools(tools)

    # Node 1: Agent calls mCP tools
    def call_agent(state: AgentState):
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    # Node 2 Sysntheize into strucutured Pydantic report
    def synthesize_report(state: AgentState):
        synthesis_prompt = """
        Based on all the tool results in this conversation, generate a structured skill report.

        Rules:
        - top_skills: exactly 3 entries, most important first
        - fastest_growing: include the skill name and specific growth signal from search results
        - declining_skills: only include if evidence found, otherwise empty list
        - action_plan: sharp and specific, no genericd advice like "keep learning"
        - mcp_insight: must reference MCP's 97M installs milestone and what it signals in hiring

        Output FORMAT: Output ONLY a valid JSON object with the schema. No markdown headers, no explanations.
        """

        message = state["messages"] + [HumanMessage(content=synthesis_prompt)]
        # Get raw response and parse manually
        raw_response = llm.invoke(message)
        parser = MarkdownJsonOutputParser()
        report = parser.parse(raw_response.content)
        return {"final_report": report}

    # Graph
    graph = StateGraph(AgentState)
    graph.add_node("agent", call_agent)
    graph.add_node("tools", ToolNode(tools))
    graph.add_node("report", synthesize_report)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent", tools_condition, {"tools": "tools", END: "report"}
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("report", END)

    return graph.compile(), client


# Pretty Print Report


def print_report(report: SkillReport):
    print("\n" + "=" * 60)
    print(f"   AI Skill Roadmap - {report.role}")
    print("+" * 60)

    print("\n🔥 Top Skills to Learn Now")
    for i, s in enumerate(report.top_skills, 1):
        print(f" {i}. {s.name} - {s.why}")

    print(f"\n📈 Fastest Growing\n {report.fastest_growing}")

    if report.declining_skills:
        print(f"\n⚠️Losing Ground\n {', '.join(report.declining_skills)}")

    print(f"\n💡Action Plan\n {report.action_plan}")

    print(f"\n🔗MCP Insight \n {report.mcp_insight}")

    print(f"\n📊 {report.data_source}")
    print("=" * 60 + "\n")


async def analyze(query: str):
    agent, client = await build_agent()

    result = await agent.ainvoke({
        "messages": [
            SystemMessage(content=(
                "You are a job market analyst specializing in AI/ML skills. "
                "Use ALL available tools to answer the user's query. "
                "Always call get_trending_skills first, then get_job_demand for "
                "specific skills mentioned, and compare_skills if comparison is needed. "
                "Call at least 3 tools before finishing."
            )),
            HumanMessage(content=query)
        ],
        "final_report": None
    })
    report = result["final_report"]
    if report:
        print_report(report)
    return report


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "I'm a Python Developer, Cloud Software Engineer and Architect, Platform Engineering in a large IT services firm. "
        "What AI skills should I prioritize in 2026 to stay hireable? "
        "Also compare MCP vs Langchain for my situation"
    )
    asyncio.run(analyze(query))
    print("\n🔥 Top skills to learn Now")
