import asyncio
import json
import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from tavily import TavilyClient
from langgraph.graph import StateGraph, START, END
from research_copilot_server.dependencies.model import model
from research_copilot_server.schema.report import model_output
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from research_copilot_server.services.retrieval import knowledge_search as run_knowledge_search

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
MAX_SEARCH_COUNT = 3
MAX_TOOL_RESULT_CHARS = 2000
MAX_MODEL_CONTEXT_CHARS = 6000

class ResearchState(TypedDict):
    query: str
    plan: str
    research: str
    messages: Annotated[list, add_messages]
    search_count: int
    title: str
    summary: str
    content: str
    sources: list[dict]



@tool
async def web_search(query: str) -> str:
    """Search the web for information relevant to the research query."""
    if tavily_client is None:
        return json.dumps({"error": "TAVILY_API_KEY is not configured"})

    result = await asyncio.to_thread(
        tavily_client.search,
        query=query,
        search_depth="advanced",
        max_results=5,
        include_answer=True,
    )
    compact_result = {
        "answer": result.get("answer"),
        "results": [
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "content": item.get("content", "")[:500],
            }
            for item in result.get("results", [])[:3]
        ],
    }
    return json.dumps(compact_result)[:MAX_TOOL_RESULT_CHARS]
    return json.dumps(compact_result)


def _web_source_from_item(item: dict) -> dict:
    return {
        "title": item.get("title") or "Web source",
        "url": item.get("url"),
        "source_type": "web",
        "metadata": {},
    }


@tool
def knowledge_search(query: str) -> str:
    """Search uploaded document chunks for information relevant to the research query."""
    results = json.loads(run_knowledge_search(query))
    compact_results = [
        {
            "content": result.get("content", "")[:800],
            "metadata": result.get("metadata", {}),
            "similarity": result.get("similarity"),
        }
        for result in results[:2]
    ]
    return json.dumps(compact_results)


def _document_source_from_result(result: dict) -> dict:
    metadata = result.get("metadata") or {}
    title = metadata.get("source") or "Uploaded document"
    return {
        "title": title,
        "url": None,
        "source_type": "document",
        "metadata": {k: v for k, v in metadata.items() if k != "source"},
    }


research_tools = [web_search, knowledge_search]
tool_node = ToolNode(research_tools)


def _message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    return json.dumps(content)


def _research_context(messages: list[BaseMessage]) -> str:
    evidence: list[str] = []
    for message in messages:
        message_type = message.type
        if message_type in {"tool", "ai"} and _message_text(message).strip():
            evidence.append(f"[{message_type}]\n{_message_text(message)}")
    context = "\n\n".join(evidence)
    return context[-MAX_MODEL_CONTEXT_CHARS:]


def _messages_for_model(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Keep the user query and newest evidence while bounding provider input size."""
    user_message = next(
        (message for message in messages if message.type == "human"),
        HumanMessage(content="Please use the available research evidence to answer the query."),
    )
    user_text = _message_text(user_message)
    remaining = max(0, MAX_MODEL_CONTEXT_CHARS - len(user_text))
    recent: list[BaseMessage] = []

    for message in reversed(messages):
        if message is user_message:
            continue

        text = _message_text(message)
        if remaining <= 0:
            break

        if len(text) > remaining:
            message = message.model_copy(update={"content": text[-remaining:]})
            text = _message_text(message)

        recent.append(message)
        remaining -= len(text)

    return [user_message, *reversed(recent)]


async def researcher(state: ResearchState):
    research_model = model.bind_tools(research_tools)
    messages = list(state.get("messages", []))
    source_list = list(state.get("sources", []))
    if not messages:
        messages.append(
            HumanMessage(
                content=(
    f"We have this query: {state['query']}\n"
    f"Use this plan to research it:\n{state['plan']}\n"
    "Use knowledge_search for uploaded documents and web_search for external information. "
    "Use the available tools to gather enough evidence to answer the query. "
    "Treat tool results as evidence. When knowledge_search returns relevant "
    "document chunks, use those chunks to answer the query. Do not claim that "
    "information is absent from the uploaded documents if a relevant tool result contains it. "
    "After reviewing tool results, decide whether more research is needed. "
    "If more information is needed, use the appropriate tool again. "
    "Once you have enough evidence, provide the research findings based only "
    "on the gathered evidence."
)
            )
        )

    response = await research_model.ainvoke(_messages_for_model(messages))
    messages.append(response)

    for message in messages:
        if getattr(message, "type", None) != "tool":
            continue
        raw = _message_text(message)
        if not isinstance(raw, str):
            continue
        try:
            payload = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            for item in payload["results"]:
                source_list.append(_web_source_from_item(item))
        elif isinstance(payload, list):
            for item in payload:
                source_list.append(_document_source_from_result(item))

    unique_sources = {
        (
            source["source_type"],
            source.get("url"),
            source["title"],
            json.dumps(source.get("metadata", {}), sort_keys=True),
        ): source
        for source in source_list
    }

    return {
        "messages": messages if len(state.get("messages", [])) == 0 else [response],
        "research": _research_context(messages),
        "sources": source_list,
        "sources": list(unique_sources.values()),
    }

async def planner(state: ResearchState):
    response = await model.ainvoke(
        f"We have this query: {state['query']}\n"
        "Create a clear plan to answer this query."
    )
    return {"plan": response.content}


structured_writer = model.with_structured_output(model_output)

async def writer(state: ResearchState):
    research_context = _research_context(list(state.get("messages", [])))
    response = await structured_writer.ainvoke(
        f"We have this query: {state['query']}\n"
        f"Use all of this research evidence to write the answer:\n{research_context}\n"
        "Return a polished response with a title, summary, and detailed content."
    )
    return {
        "title": response.title,
        "summary": response.summary,
        "content": response.content,
    }
def should_continue(state: ResearchState):
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None) and state.get("search_count", 0) < MAX_SEARCH_COUNT:
        return "tools"
    return "writer"


def increment_search_count(state: ResearchState):
    return {"search_count": state.get("search_count", 0) + 1}
    


builder = StateGraph(ResearchState)

builder.add_node("planner", planner)
builder.add_node("researcher", researcher)
builder.add_node("writer", writer)
builder.add_node("tools", tool_node)
builder.add_node("increment_search_count", increment_search_count)

builder.add_edge(START, "planner")
builder.add_edge("planner", "researcher")

builder.add_conditional_edges(
    "researcher",
    should_continue,
    {
        "tools": "tools",
        "writer": "writer",
    }
)

builder.add_edge("tools", "increment_search_count")
builder.add_edge("increment_search_count", "researcher")

builder.add_edge("writer", END)

workflow = builder.compile()
