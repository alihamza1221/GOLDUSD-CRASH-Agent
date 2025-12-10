import os
from datetime import datetime
from typing import TypedDict, Annotated, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

# Import tools
from tools import get_xauusd_data, get_gold_news_newsapi, search_perplexity

load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Define the agent state
class AgentState(TypedDict):
    messages: list
    tools_output: dict
    analysis_type: str  # 'trend', 'lower_limit', 'upper_limit', 'general'
    final_answer: str

# System prompts for different analysis types
TREND_SYSTEM_PROMPT = """You are a GOLDUSD CRASH EXPERT specializing in market trend analysis.

Analyze the provided market data, news, and search results to determine the gold market trend for THIS WEEK.

Your response MUST be in this EXACT format:
TREND: [bullish|bearish|consolidation]

Analysis rules:
- bullish: Price above MA20 and MA50, positive momentum, supportive news
- bearish: Price below MA20 and MA50, negative momentum, risk-off sentiment
- consolidation: Price range-bound, mixed signals, low volatility

Provide ONLY the format above, nothing else."""

LOWER_LIMIT_SYSTEM_PROMPT = """You are a GOLDUSD CRASH EXPERT specializing in support level detection.

Analyze the provided market data to identify the STRONGEST SUPPORT LEVEL where gold could reverse after a downward move THIS WEEK.

Your response MUST be in this EXACT format:
LIMIT: $XXXX.XX

Consider:
- Fibonacci 50% retracement level
- Recent 20-day lows
- Volume clusters at support zones
- DXY correlation (inverse)

Choose the MOST LIKELY support level that will hold this week. Provide ONLY the format above, nothing else."""

UPPER_LIMIT_SYSTEM_PROMPT = """You are a GOLDUSD CRASH EXPERT specializing in resistance level detection.

Analyze the provided market data to identify the STRONGEST RESISTANCE LEVEL where gold could reverse after an upward move THIS WEEK.

Your response MUST be in this EXACT format:
LIMIT: $XXXX.XX

Consider:
- 50-EMA resistance
- Recent 20-day highs
- Volume clusters at resistance zones
- Major psychological levels

Choose the MOST LIKELY resistance level that will cap moves this week. Provide ONLY the format above, nothing else."""

GENERAL_SYSTEM_PROMPT = """You are a GOLDUSD CRASH EXPERT with deep knowledge of:
- Market trend analysis and technical indicators
- Strong support and resistance levels
- Fundamental factors affecting gold prices

Use the available tools to gather data and provide comprehensive answers about GOLDUSD/gold market analysis.

Skills:
1. Market Trend Analyzer - Determine market phase (bullish/bearish/consolidation)
2. Lower Bound Detector - Identify maximum downside support (LOWER CRASH LIMIT)
3. Upper Bound Detector - Identify maximum upside resistance (UPPER CRASH LIMIT)

Provide clear, actionable insights based on technical and fundamental analysis."""


def call_tools(state: AgentState) -> AgentState:
    """Call all tools to gather comprehensive data"""
    tools_output = {}
    
    # Get market data
    try:
        # Call the tool's invoke method (LangChain StructuredTool pattern)
        market_data = get_xauusd_data.invoke({})
        tools_output['market_data'] = market_data
    except Exception as e:
        tools_output['market_data'] = {"error": str(e)}
    
    # Get news
    try:
        # Call the tool's invoke method
        news_data = get_gold_news_newsapi.invoke({})
        tools_output['news'] = news_data
    except Exception as e:
        tools_output['news'] = {"error": str(e)}
    
    # Get search results based on analysis type
    try:
        if state['analysis_type'] == 'trend':
            search_query = "What is the current gold market trend to continue today? Bullish or bearish or consolidation sentiment to maintain today?"
        elif state['analysis_type'] == 'lower_limit':
            search_query = "What is price if gold fall below that it could further crash today? First Support level that gold should respect today?"
        elif state['analysis_type'] == 'upper_limit':
            search_query = "What is price if gold rise above that it could face major sell pressure today? First Resistance level today that gold should respect?"
        else:
            # Extract query from messages
            search_query = state['messages'][-1].content if state['messages'] else "Gold market analysis"
        
        # Call the tool's invoke method with the query
        search_results = search_perplexity.invoke({"query": search_query})
        tools_output['search'] = search_results
    except Exception as e:
        tools_output['search'] = {"error": str(e)}
    
    state['tools_output'] = tools_output
    return state


def analyze(state: AgentState) -> AgentState:
    """Analyze the data and generate response"""
    analysis_type = state['analysis_type']
    tools_output = state['tools_output']
    
    # Select appropriate system prompt
    if analysis_type == 'trend':
        system_prompt = TREND_SYSTEM_PROMPT
    elif analysis_type == 'lower_limit':
        system_prompt = LOWER_LIMIT_SYSTEM_PROMPT
    elif analysis_type == 'upper_limit':
        system_prompt = UPPER_LIMIT_SYSTEM_PROMPT
    else:
        system_prompt = GENERAL_SYSTEM_PROMPT
    
    # Prepare context from tools
    context = f"""
DATA GATHERED:

Market Data:
{tools_output.get('market_data', 'N/A')}

News Headlines:
{tools_output.get('news', 'N/A')}

Market Intelligence:
{tools_output.get('search', 'N/A')}

Based on this data, provide your analysis.
"""

    print("Context for analysis:", context)
    
    # Create messages
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=context)
    ]
    
    # Get LLM response
    response = llm.invoke(messages)
    state['final_answer'] = response.content
    
    return state


# Build the graph
def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("gather_data", call_tools)
    workflow.add_node("analyze", analyze)
    
    # Add edges
    workflow.set_entry_point("gather_data")
    workflow.add_edge("gather_data", "analyze")
    workflow.add_edge("analyze", END)
    
    return workflow.compile()


# Create the agent
agent = create_agent_graph()


def run_trend_analysis() -> str:
    """Run trend analysis for gold this week"""
    initial_state = {
        "messages": [],
        "tools_output": {},
        "analysis_type": "trend",
        "final_answer": ""
    }
    
    result = agent.invoke(initial_state)
    return result['final_answer']


def run_lower_limit_analysis() -> str:
    """Run lower crash limit analysis"""
    initial_state = {
        "messages": [],
        "tools_output": {},
        "analysis_type": "lower_limit",
        "final_answer": ""
    }
    
    result = agent.invoke(initial_state)
    return result['final_answer']


def run_upper_limit_analysis() -> str:
    """Run upper crash limit analysis"""
    initial_state = {
        "messages": [],
        "tools_output": {},
        "analysis_type": "upper_limit",
        "final_answer": ""
    }
    
    result = agent.invoke(initial_state)
    return result['final_answer']


def run_general_query(query: str) -> str:
    """Run general query analysis"""
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "tools_output": {},
        "analysis_type": "general",
        "final_answer": ""
    }
    
    result = agent.invoke(initial_state)
    return result['final_answer']


if __name__ == "__main__":
    print("Testing Gold Crash Expert Agent...")
    print("\n1. Trend Analysis:")
    print(run_trend_analysis())
    print("\n2. Lower Limit:")
    print(run_lower_limit_analysis())
    print("\n3. Upper Limit:")
    print(run_upper_limit_analysis())
