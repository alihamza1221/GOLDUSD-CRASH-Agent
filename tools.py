import os
import yfinance
import requests
from datetime import datetime, timedelta
from langchain_core.tools import tool
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


@tool
def get_market_data(symbol: str = "GOLDUSD"):
    """
    Fetch comprehensive market data for any trading symbol using Perplexity AI for real-time analysis.
    Args:
        symbol: Trading symbol (e.g., GOLDUSD, EURUSD, BTCUSD, AAPL, etc.)
    Returns: Market data with current price, technical levels, and market context
    """
    
    try:
        # Use Perplexity to get real-time market data
        client = OpenAI(
            api_key=os.getenv("PERPLEXITY_API_KEY"),
            base_url="https://api.perplexity.ai"
        )
        
        query = f"""What is the current {symbol} price right now considering post/pre market hours? Provide:
1. Current price for {symbol} considering post/pre market hours.
2. Key support levels from where {symbol} can go down.
3. Key resistance levels from where {symbol} can face selling pressure.
4. Recent volume trend (higher/lower than average)
5. Overall market sentiment (bullish/bearish/consolidation) for active week.

Format the response as structured data with clear labels."""
        
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a real-time financial data provider. Extract current {symbol} market data and technical levels considering post/pre market hours. Provide precise numerical values. make the response consise and factual."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        
        market_analysis = response.choices[0].message.content
        print(f"Real-time {symbol} Data:\n{market_analysis}")
        
        market_data = {
            "raw_analysis": market_analysis,
            "timestamp": datetime.now().isoformat(),
            "data_source": "Perplexity AI (Real-time) search",
            "symbol": symbol,
            "status": "success"
        }
        
        return market_data
    
    except Exception as e:
        return {"error": f"Failed to fetch {symbol} data via Perplexity: {str(e)}", "status": "error"}


@tool
def search_perplexity(query: str, symbol: str = "GOLDUSD"):
    """
    Search for real-time market intelligence using Perplexity API.
    Useful for getting current market sentiment, analyst opinions, and breaking news.
    Args:
        query: The search query for market intelligence
        symbol: Trading symbol for context (e.g., GOLDUSD, EURUSD, BTCUSD)
    """
    try:
        
        # Perplexity uses OpenAI-compatible API
        client = OpenAI(
            api_key=os.getenv("PERPLEXITY_API_KEY"),
            base_url="https://api.perplexity.ai"
        )
        
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a real-time financial data provider. Extract current {symbol} market data and technical levels considering post/pre market hours. Provide precise numerical values. make the response consise and factual and latest."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        
        return {
            "query": query,
            "symbol": symbol,
            "answer": response.choices[0].message.content,
            "status": "success"
        }
    except Exception as e:
        return {
            "query": query,
            "symbol": symbol,
            "error": f"Failed to search: {str(e)}",
            "status": "error"
        }


print("✓ Market data tool loaded (supports any symbol)")
