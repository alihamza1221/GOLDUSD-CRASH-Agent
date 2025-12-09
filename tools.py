import os
import yfinance
import requests
from datetime import datetime, timedelta
from langchain_core.tools import tool
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


@tool
def get_xauusd_data(**kwargs):
    """
    Fetch comprehensive XAUUSD (Gold) market data using Perplexity AI for real-time analysis.
    Returns: Market data with current price, technical levels, and market context
    """
    
    try:
        # Use Perplexity to get real-time gold market data
        client = OpenAI(
            api_key=os.getenv("PERPLEXITY_API_KEY"),
            base_url="https://api.perplexity.ai"
        )
        
        query = """What is the current GOLDUSD (Gold) price right now considering post/pre market hours? Provide:
1. Current futures price for GOLDUSD considering post/pre market hours.
2. Key support levels from where gold can go down.
3. Key resistance levels from where gold can face selling pressure.
4. Recent volume trend (higher/lower than average)
5. Overall market sentiment (bullish/bearish/consolidation) for active week.

Format the response as structured data with clear labels."""
        
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {
                    "role": "system",
                    "content": "You are a real-time financial data provider. Extract current gold market data and technical levels considering post/pre market hours. Provide precise numerical values. make the response consise and factual."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        
        market_analysis = response.choices[0].message.content
        print(f"Real-time XAUUSD Data:\n{market_analysis}")
        
        market_data = {
            "raw_analysis": market_analysis,
            "timestamp": datetime.now().isoformat(),
            "data_source": "Perplexity AI (Real-time) search",
            "symbol": "GOLDUSD",
            "status": "success"
        }
        
        return market_data
    
    except Exception as e:
        return {"error": f"Failed to fetch GOLDUSD data via Perplexity: {str(e)}", "status": "error"}


@tool
def get_gold_news_newsapi():
    """Get latest gold-related news from NewsAPI for the past week"""
    api_key = os.getenv('NEWS_API_KEY')
    today = datetime.now()
    week_ago = today - timedelta(days=1)
    
    url = "https://newsapi.org/v2/everything"
    
    params = {
        "q": "gold OR XAUUSD OR precious metals OR gold price",
        "language": "en",
        "sortBy": "publishedAt",
        "from": week_ago.strftime('%Y-%m-%d'),
        "to": today.strftime('%Y-%m-%d'),
        "apiKey": api_key,
        "pageSize": 2
    }
    
    response = requests.get(url, params=params,timeout=50)
    data = response.json()
    try:        

      if data['status'] == 'ok':
          if data['status'] == 'ok':
              articles = []
              for article in data['articles']:
                  articles.append({
                      "title": article['title'],
                      "description": article['description'],
                      "url": article['url'],
                      "source": article['source']['name'],
                      "published_at": article['publishedAt'],
                      "content_snippet": article.get('content', '')[:200]
                  })

              return {
                  "total_results": data['totalResults'],
                  "articles": articles,
                  "status": "success"
              }
          else:
              return {"error": data.get('message', 'Unknown error')}
    except Exception as e:
        return {"error": f"Failed to fetch news: {str(e)}"}


@tool
def search_perplexity(query: str):
    """
    Search for real-time market intelligence using Perplexity API.
    Useful for getting current market sentiment, analyst opinions, and breaking news.
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
                    "content": "You are a real-time financial data provider. Extract current gold market data and technical levels considering post/pre market hours. Provide precise numerical values. make the response consise and factual and latest."
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        
        return {
            "query": query,
            "answer": response.choices[0].message.content,
            "status": "success"
        }
    except Exception as e:
        return {
            "query": query,
            "error": f"Failed to search: {str(e)}",
            "status": "error"
        }


print("✓ XAUUSD market data tool loaded")
print("✓ Financial news API tool loaded")
print("✓ Perplexity search tool loaded")