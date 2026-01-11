import os
from datetime import datetime
from typing import TypedDict, Annotated, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

# Import tools
from tools import get_market_data, search_perplexity

load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-5.2",
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Define the agent state
class AgentState(TypedDict):
    messages: list
    tools_output: dict
    analysis_type: str  # 'trend', 'lower_limit', 'upper_limit', 'general'
    symbol: str  # Trading symbol (e.g., GOLDUSD, EURUSD, BTCUSD)
    final_answer: str


def get_trend_system_prompt(symbol: str) -> str:
    """Generate trend analysis system prompt for any symbol"""
    return f"""You are a {symbol} FUTURES CRASH EXPERT specializing in market trend analysis.

Analyze the provided market data, news, and search results to determine the {symbol} market trend for THIS WEEK.

Your response MUST be in this EXACT format:
TREND: [bullish|bearish|consolidation]

Analysis rules:
- bullish: positive momentum
- bearish: negative momentum, risk-off sentiment
- consolidation: Price range-bound, mixed signals, low volatility

Provide ONLY the format above, nothing else."""


def get_lower_limit_system_prompt(symbol: str) -> str:
    """Generate lower limit analysis system prompt for any symbol"""
    return f"""You are a {symbol} CRASH EXPERT specializing in support level detection.

Analyze the provided market data to identify the near SUPPORT LEVEL where {symbol} could reverse after a downward move THIS WEEK.

Your response MUST be in this EXACT format:
LIMIT: $XXXX.XX

Consider:
- Volume clusters at support zones
- Correlation with related markets

Choose the MOST LIKELY support level that will hold to before seeing any retracement. Provide ONLY the format above, nothing else."""


def get_upper_limit_system_prompt(symbol: str) -> str:
    """Generate upper limit analysis system prompt for any symbol"""
    return f"""You are a {symbol} levels EXPERT specializing in near resistance level detection.

Analyze the provided market data to identify the near RESISTANCE LEVEL where {symbol} could reverse after an upward move THIS WEEK.

Your response MUST be in this EXACT format:
LIMIT: $XXXX.XX

Consider:
- Volume clusters at resistance zones
- Major psychological levels

Choose the MOST LIKELY near resistance level that will cap moves this week before seeing any retracement. Provide ONLY the format above, nothing else."""


def get_general_system_prompt(symbol: str) -> str:
    """Generate general analysis system prompt for any symbol"""
    return f"""You are a {symbol} CRASH EXPERT with deep knowledge of:
- Market trend analysis and technical indicators
- Strong support and resistance levels
- Fundamental factors affecting {symbol} prices

Use the available tools to gather data and provide comprehensive answers about {symbol} market analysis.

Skills:
1. Market Trend Analyzer - Determine market phase (bullish/bearish/consolidation)
2. Lower Bound Detector - Identify maximum downside support (LOWER CRASH LIMIT)
3. Upper Bound Detector - Identify maximum upside resistance (UPPER CRASH LIMIT)

Provide clear, actionable insights based on technical and fundamental analysis."""


def call_tools(state: AgentState) -> AgentState:
    """Call all tools to gather comprehensive data"""
    tools_output = {}
    symbol = state.get('symbol', 'GOLDUSD')
    
    # Get market data
    try:
        # Call the tool's invoke method (LangChain StructuredTool pattern)
        market_data = get_market_data.invoke({"symbol": symbol})
        tools_output['market_data'] = market_data
    except Exception as e:
        tools_output['market_data'] = {"error": str(e)}
    
    # Get search results based on analysis type
    try:
        if state['analysis_type'] == 'trend':
            search_query = f"What is the current {symbol} market trend to continue today? Bullish or bearish or consolidation sentiment to maintain today?"
        elif state['analysis_type'] == 'lower_limit':
            search_query = f"What is price if {symbol} fall below that it could further crash today? First Support level that {symbol} should respect today?"
        elif state['analysis_type'] == 'upper_limit':
            search_query = f"What is price if {symbol} rise above that it could face major sell pressure today? First Resistance level today that {symbol} should respect?"
        else:
            # Extract query from messages
            search_query = state['messages'][-1].content if state['messages'] else f"{symbol} market analysis"
        
        # Call the tool's invoke method with the query and symbol
        search_results = search_perplexity.invoke({"query": search_query, "symbol": symbol})
        tools_output['search'] = search_results
    except Exception as e:
        tools_output['search'] = {"error": str(e)}
    
    state['tools_output'] = tools_output
    return state


def analyze(state: AgentState) -> AgentState:
    """Analyze the data and generate response"""
    analysis_type = state['analysis_type']
    tools_output = state['tools_output']
    symbol = state.get('symbol', 'GOLDUSD')
    
    # Select appropriate system prompt
    if analysis_type == 'trend':
        system_prompt = get_trend_system_prompt(symbol)
    elif analysis_type == 'lower_limit':
        system_prompt = get_lower_limit_system_prompt(symbol)
    elif analysis_type == 'upper_limit':
        system_prompt = get_upper_limit_system_prompt(symbol)
    else:
        system_prompt = get_general_system_prompt(symbol)
    
    # Prepare context from tools
    context = f"""
DATA GATHERED:

Market Data:
{tools_output.get('market_data', 'N/A')}


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


def run_trend_analysis(symbol: str = "GOLDUSD") -> str:
    """Run trend analysis for any symbol this week"""
    initial_state = {
        "messages": [],
        "tools_output": {},
        "analysis_type": "trend",
        "symbol": symbol,
        "final_answer": ""
    }
    
    result = agent.invoke(initial_state)
    return result['final_answer']


def run_lower_limit_analysis(symbol: str = "GOLDUSD") -> str:
    """Run lower crash limit analysis for any symbol"""
    initial_state = {
        "messages": [],
        "tools_output": {},
        "analysis_type": "lower_limit",
        "symbol": symbol,
        "final_answer": ""
    }
    
    result = agent.invoke(initial_state)
    return result['final_answer']


def run_upper_limit_analysis(symbol: str = "GOLDUSD") -> str:
    """Run upper crash limit analysis for any symbol"""
    initial_state = {
        "messages": [],
        "tools_output": {},
        "analysis_type": "upper_limit",
        "symbol": symbol,
        "final_answer": ""
    }
    
    result = agent.invoke(initial_state)
    return result['final_answer']


def run_general_query(query: str, symbol: str = "GOLDUSD") -> str:
    """Run general query analysis for any symbol"""
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "tools_output": {},
        "analysis_type": "general",
        "symbol": symbol,
        "final_answer": ""
    }
    
    result = agent.invoke(initial_state)
    return result['final_answer']


if __name__ == "__main__":
    print("Testing Market Crash Expert Agent...")
    symbol = "GOLDUSD"
    print(f"\nTesting with symbol: {symbol}")
    print("\n1. Trend Analysis:")
    print(run_trend_analysis(symbol))
    print("\n2. Lower Limit:")
    print(run_lower_limit_analysis(symbol))
    print("\n3. Upper Limit:")
    print(run_upper_limit_analysis(symbol))
