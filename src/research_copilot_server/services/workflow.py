from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from research_copilot_server.dependencies.model import model
from research_copilot_server.schema.report import model_output


class ResearchState(TypedDict):
    query: str
    plan: str
    research: str
    title: str
    summary: str
    content: str


async def researcher(state: ResearchState):
    response = await model.ainvoke(
        f"We have this query: {state['query']}\n"
        f"Use this plan to research it:\n{state['plan']}\n"
        "Provide thorough, factual research findings."
    )
    return {"research": response.content}

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

    



builder = StateGraph(ResearchState)

builder.add_node("planner", planner)
builder.add_node("researcher", researcher)
builder.add_node("writer", writer)

builder.add_edge(START, "planner")
builder.add_edge("planner", "researcher")
builder.add_edge("researcher", "writer")
builder.add_edge("writer", END)

workflow = builder.compile()

