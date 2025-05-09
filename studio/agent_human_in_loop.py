from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode

# Nodefrom langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import MemorySaver


def add(a: int, b: int) -> int:
    """Adds a and b.

    Args:
        a: first int
        b: second int
    """
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiplies a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b


def divide(a: int, b: int) -> float:
    """Divide a and b.

    Args:
        a: first int
        b: second int
    """
    return a / b


tools = [add, multiply, divide]

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
        content="You are a helpful assistant tasked with writing performing arithmetic on a set of inputs."
    )
    return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}


# Graph
builder = StateGraph(MessagesState)

# Define nodes: these do the work
builder.add_node("assistant", assistant)
builder.add_node("confirm", confirm)
builder.add_node("tools", ToolNode(tools))

# Define edges: these determine how the control flow moves
builder.add_edge(START, "confirm")
builder.add_edge("confirm", "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "assistant")


graph = builder.compile(interrupt_before=["assistant"])
