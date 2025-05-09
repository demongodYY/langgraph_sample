from typing import Annotated

from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END


alert_log = """
2025-04-07 14:32:17.521 [INFO] [http-nio-8080-exec-45]
com.example.api.PaymentController - 
[UserAction] Received payment request: userId=U123094, amount=¥289.00, method=WeChatPay, clientIp=223.91.**.**

2025-04-07 14:32:17.529 [DEBUG] [TransactionProcessor-Worker-14]
com.example.payment.transaction.TransactionService - 
[InitTransaction] Initializing transaction for userId=U123094, cartId=C94833012

2025-04-07 14:32:17.539 [INFO] [TransactionProcessor-Worker-14]
com.example.payment.repository.TransactionRepository - 
[DB_WRITE] Inserting new transaction record: TXN-202504071432-889331245 into `payment_transaction` table

2025-04-07 14:32:17.552 [DEBUG] [HikariCP-ConnectionPool-1]
com.zaxxer.hikari.pool.HikariPool - 
[DB_POOL] Connection acquired in 4ms, thread=TransactionProcessor-Worker-14

2025-04-07 14:32:17.575 [INFO] [TransactionProcessor-Worker-14]
com.example.payment.gateway.ExternalGatewayClient - 
[GatewayRequest] Sending payment initiation to WeChatPay:
  URL: https://api.wechatpay.cn/v1/payments
  Method: POST
  Payload: {
    "transaction_id": "TXN-202504071432-889331245",
    "amount": 28900,
    "currency": "CNY",
    "user_id": "U123094"
  }
  Headers: Authorization: Bearer ***

2025-04-07 14:32:22.824 [ERROR] [TransactionProcessor-Worker-14]
com.example.payment.gateway.ExternalGatewayClient - 
[Timeout] No response from WeChatPay gateway within 5000ms (requestId=GW-REQ-202504071432-1988301)

2025-04-07 14:32:22.825 [WARN] [TransactionProcessor-Worker-14]
com.example.payment.transaction.TransactionProcessor - 
[TransactionFailed] External payment initiation failed, retrying (attempt 1/3)

2025-04-07 14:32:28.014 [ERROR] [TransactionProcessor-Worker-14]
com.example.payment.transaction.TransactionProcessor - 
[TXN_PROC_503_TIMEOUT] Payment failed after 3 retries. Marking transaction as FAILED.
TransactionId=TXN-202504071432-889331245, Error=ExternalGatewayTimeoutException

2025-04-07 14:32:28.019 [INFO] [TransactionProcessor-Worker-14]
com.example.payment.repository.TransactionRepository - 
[DB_UPDATE] Updating transaction status to FAILED for TXN-202504071432-889331245

2025-04-07 14:32:28.024 [INFO] [http-nio-8080-exec-45]
com.example.api.PaymentController - 
[Response] Returning failure response to client:
  {
    "status": "failed",
    "message": "支付请求超时，请稍后重试。",
    "errorCode": "TXN_PROC_503_TIMEOUT"
  }
""".strip()

# Web search tool
from langchain_community.tools.tavily_search import TavilySearchResults


@tool
def search_web(query: str):
    """Retrieve docs from web search

    Args:
        query: the question to search
    """

    # Search
    tavily_search = TavilySearchResults(max_results=3)

    # Search query

    # Search
    search_docs = tavily_search.invoke(query)

    # Format
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document href="{doc["url"]}"/>\n{doc["content"]}\n</Document>'
            for doc in search_docs
        ]
    )

    return formatted_search_docs


from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0.0)


class AgentState(MessagesState):
    log: str
    summary: str


class InputState(MessagesState):
    log: str


class Agent:
    def __init__(self):
        graph = StateGraph(AgentState, input=InputState, output=MessagesState)
        self.tools = [search_web]

        graph.add_node("init_summary", self.init_summary_node)
        graph.add_node("action_confirm", self.action_confirm_node)
        graph.add_node("query_agent", self.query_agent_node)
        graph.add_node("query_tools", self.query_tools_node)
        graph.add_node("action_taken", self.action_taken_node)

        graph.add_conditional_edges(
            START,
            self.is_action,
            {
                "ACTION_INPUT": "action_confirm",
                "QUERY_INPUT": "query_agent",
                "INIT_SUMMARY": "init_summary",
            },
        )
        graph.add_edge("init_summary", END)
        graph.add_edge("action_confirm", "action_taken")
        graph.add_edge("action_taken", END)
        graph.add_conditional_edges(
            "query_agent",
            self.exists_tools_calling,
            {True: "query_tools", False: END},
        )
        graph.add_edge("query_tools", "query_agent")
        self.graph = graph.compile(interrupt_before=["action_taken"])

    def is_init_summary(self, state: AgentState):
        if len(state["messages"]) == 0:
            return True
        else:
            return False

    def init_summary_node(self, state: AgentState):
        if "summary" not in state:
            sumary_prompt = SystemMessage(
                content="""
You are a system operation expert. You should read the log and summarize the system operation status.
The summary should include:
- Summary title
- Situation summary
- Call chain analyst
- Root cause analysis 

Output should be conciese and clear, less than 300 words
""".strip()
            )
            summary = llm.invoke([sumary_prompt, HumanMessage(content=state["log"])])
            return {"summary": summary.content, "messages": [summary]}
        else:
            return state

    def is_action(self, state: AgentState):
        if len(state["messages"]) == 0:
            return "INIT_SUMMARY"
        classify_prompt = SystemMessage(
            content="""
You are a smart assistant. You should classify the log into two categories: action and query.
Only return the category name (query or action), nothing else.                                        
""".strip()
        )
        result = llm.invoke([classify_prompt] + state["messages"])
        route_state = "ACTION_INPUT" if result.content == "action" else "QUERY_INPUT"
        return route_state

    def action_confirm_node(self, state: AgentState):
        # System message
        sys_msg = SystemMessage(
            content="What ever user asked, you should confirm it by a rhetorical question and highlight the action should be taken."
        )

        return {"messages": [llm.invoke([sys_msg] + state["messages"])]}

    def action_taken_node(self, state: AgentState):
        return {"messages": [AIMessage(content="Action done")]}

    def query_agent_node(self, state: AgentState):
        sys_prompt = SystemMessage(
            content="""
You are a system operation expert. You should troubleshooting and answer user's query.
You should search on the web before you answer the question. If you can not find the answer, please say "I don't know".

When answering questions, follow these guidelines:
        
1. Use only the information provided in the context. 
        
2. Do not introduce external information or make assumptions beyond what is explicitly stated in the context.

3. The context contain sources at the topic of each individual document.

4. Include these sources your answer next to any relevant statements. For example, for source # 1 use [1]. 

5. List your sources in order at the bottom of your answer. [1] Source 1, [2] Source 2, etc
        
6. If the source is: <Document source="assistant/docs/llama3_1.pdf" page="7"/>' then just list: 
        
[1] assistant/docs/llama3_1.pdf, page 7 
        
And skip the addition of the brackets as well as the Document source preamble in your citation.
""".strip()
        )

        message = llm.bind_tools(self.tools).invoke([sys_prompt] + state["messages"])

        return {"messages": [message]}

    def query_tools_node(self, state: AgentState):
        tool_calls = state["messages"][-1].tool_calls
        results = []

        for t in tool_calls:
            print(f"Calling: {t}")
            result = self.tools[0].invoke(t["args"])
            message = ToolMessage(
                content=str(result), tool_call_id=t["id"], name=t["name"]
            )
            results.append(message)

        return {"messages": results}

    def exists_tools_calling(self, state: AgentState):
        result = state["messages"][-1]
        return len(result.tool_calls) > 0


graph = Agent().graph
