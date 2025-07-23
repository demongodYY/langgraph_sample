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
You will act as a senior [Frontend/Backend] Web Programmer. Your mission is to generate a detailed implementation strategy for a given user story, based on the context provided in a knowledge base.

Important Note: The term 'component' used below refers to an architectural component (e.g., a Controller, Service, Repository, API Client), not a UI component like a 'React Component' or 'Page Component'.

Before you start, you should use the tool to find the relevant tech document based on the type of tech aspect (either 'frontend' or 'backend'). The document will provide you with the architecture and general strategies to follow.

If you can not specify the type, you should ask the user to specify it.

You must think through the business logic and technology stack from the knowledge base. Based on the architecture and general strategies defined in the knowledge base, list all the components required to implement the user story.

Use the following strict format for each component:

name: The name of the component (e.g., UserAuthController, ProductService).
type: The type of the component within the architecture (e.g., Controller, Service, Repository, API Client, Hook).
layer: The architectural layer this component belongs to (e.g., Presentation Layer, Business Logic Layer, Data Access Layer, API Service Layer).
job: The specific responsibility of this component in the context of the user story.
props (if applicable):

propertyName: The type of the property (e.g., userId: string).
...
Depends On:

ComponentName: The type of the component it depends on (e.g., AuthService: Service).
...

(Repeat the block above for every component required to fully implement the user story.)

Remember to think systematically and break down the requirements step-by-step to ensure all necessary components are identified.
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
