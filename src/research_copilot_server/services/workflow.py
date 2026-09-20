from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, START, END
from research_copilot_server.dependencies.model import model
from research_copilot_server.schema.report import model_output
from langchain_core.tools import tool
from langgraph.graph.message import add_messages

class ResearchState(TypedDict):
    query: str
    plan: str
    research: str
    messages: Annotated[list, add_messages]
    search_count: int
    title: str
    summary: str
    content: str



@tool
async def web_search(query: str) -> str:
    """Search the web for information relevant to the research query."""
    return f"Fake search results for: {query}"


async def researcher(state: ResearchState):
    research_model = model.bind_tools([web_search])

    response = await research_model.ainvoke(
        f"We have this query: {state['query']}\n"
        f"Use this plan to research it:\n{state['plan']}\n"
        "Use web_search if you need external information. "
        "After getting the search result, provide the research findings."
    )

    return {
        "messages": [response],
        "research": response.content or "",
    }

async def planner(state: ResearchState):
    response = await model.ainvoke(
        f"We have this query: {state['query']}\n"
        "Create a clear plan to answer this query."
    )
    return {"plan": response.content}


structured_writer = model.with_structured_output(model_output)

async def writer(state: ResearchState):
    response = await structured_writer.ainvoke(
        f"We have this query: {state['query']}\n"
        f"Use this research to write the answer:\n{state['research']}\n"
        "Return a polished response with a title, summary, and detailed content."
    )
    return {
        "title": response.title,
        "summary": response.summary,
        "content": response.content,
    }
def should_continue(state: ResearchState):
    """Skip tool execution during the initial no-loop debugging pass."""
    return "writer"
    


builder = StateGraph(ResearchState)

builder.add_node("planner", planner)
builder.add_node("researcher", researcher)
builder.add_node("writer", writer)

builder.add_edge(START, "planner")
builder.add_edge("planner", "researcher")

builder.add_conditional_edges(
    "researcher",
    should_continue,
    {
        "writer": "writer",
    }
)

builder.add_edge("writer", END)

workflow = builder.compile()

