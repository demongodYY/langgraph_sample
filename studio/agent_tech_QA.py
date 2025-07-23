from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode


def find_document(type: str) -> str:
    """Finds the tech document based on the type.

    Args:
        type: the type of tech document to find only include "frontend", "backend"
    """
    if type == "frontend":
        with open("./tech_doc/frontend.md", "r", encoding="utf-8") as file:
            return file.read()  # read file from frontend.md
    elif type == "backend":
        with open("./tech_doc/backend.md", "r", encoding="utf-8") as file:
            return file.read()  # read file from backend.md
    else:
        raise ValueError("Unsupported type. Only 'frontend' and 'backend' are allowed.")


tools = [find_document]

# Define LLM with bound tools
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools)


# Node
def confirm(state: MessagesState):
    # System message
    sys_msg = SystemMessage(
        content="What ever user asked, you should confirm it by a rhetorical question."
    )

    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}


# Node
def assistant(state: MessagesState):
    sys_msg = SystemMessage(
        content="""
You will act as a senior [Frontend/Backend] Web Programmer. Should answer the user's question based on the tech document provided.
"""
    )
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}


# Graph
builder = StateGraph(MessagesState)

# Define nodes: these do the work
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "assistant")


graph = builder.compile()
