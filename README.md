# Gold Crash Expert Agent

AI-powered agent for GOLDUSD crash limit detection and market analysis using LangGraph and FastAPI.

## Overview

This project implements an intelligent agent that analyzes gold market data to identify:
- **Market Trends**: Bullish, bearish, or consolidation phases
- **Lower Crash Limits**: Strong support levels where gold may reverse after downward moves
- **Upper Crash Limits**: Strong resistance levels where gold may reverse after upward moves

## Architecture

### Components

1. **tools.py**: Market data tools
   - `get_xauusd_data()`: Fetches gold futures data with technical indicators
   - `get_gold_news_newsapi()`: Gets recent gold-related news
   - `search_perplexity()`: Real-time market intelligence via Perplexity API

2. **agent.py**: LangGraph-based agent
   - State management for different analysis types
   - Data gathering and analysis workflow
   - Specialized system prompts for each analysis type

3. **api.py**: FastAPI REST endpoints
   - `GET /trend`: Market trend analysis
   - `GET /lower-limit`: Lower crash limit (support)
   - `GET /upper-limit`: Upper crash limit (resistance)
   - `POST /query`: General queries

4. **tasks.py**: Agent configuration with skills definition

## Setup

### Prerequisites

- Python 3.8+
- Virtual environment (venv included)

### Installation

1. Activate virtual environment:
```powershell
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

3. Configure API keys in `.env`:
```env
OPENAI_API_KEY=your_openai_key
NEWS_API_KEY=your_newsapi_key
PERPLEXITY_API_KEY=your_perplexity_key
```

## Usage

### Start the API Server

```powershell
python api.py
```

Server runs on `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### API Endpoints

#### 1. Get Market Trend
```bash
GET http://localhost:8000/trend
```

Response:
```json
{
  "trend": "bullish",
  "raw_response": "TREND: bullish"
}
```

#### 2. Get Lower Crash Limit
```bash
GET http://localhost:8000/lower-limit
```

Response:
```json
{
  "limit": "$2645.50",
  "raw_response": "LIMIT: $2645.50"
}
```

#### 3. Get Upper Crash Limit
```bash
GET http://localhost:8000/upper-limit
```

Response:
```json
{
  "limit": "$4725.80",
  "raw_response": "LIMIT: $3725.80"
}
```

#### 4. Custom Query
```bash
POST http://localhost:8000/query
Content-Type: application/json

{
  "query": "What factors are affecting gold prices this week?"
}
```

Response:
```json
{
  "answer": "Detailed analysis based on market data, news, and search results..."
}
```

### Test Agent Directly

```powershell
python agent.py
```

## Data Sources

- **Market Data**: Yahoo Finance (GC=F - Gold Futures, DX=F - Dollar Index)
- **News**: NewsAPI (past 7 days of gold-related articles)
- **Intelligence**: Perplexity API (real-time market analysis)

## Technical Analysis Features

### Factor 1: Market Trend
- EMA 20 and EMA 50
- 20-day volatility
- Recent highs/lows (5-day and 20-day)
- Volume analysis

### Factor 2: Support Levels (Lower Limits)
- Fibonacci 50% retracement
- Recent 20-day lows
- Volume clusters

### Factor 3: Resistance Levels (Upper Limits)
- EMA 50 resistance
- Recent 20-day highs
- Psychological levels

### External Factors
- DXY (US Dollar Index) inverse correlation
- News sentiment
- Market intelligence

## Response Formats

All endpoint responses are structured and consistent:

- **Trend**: `bullish | bearish | consolidation`
- **Limits**: `$XXXX.XX` format
- **Queries**: Comprehensive analysis with data-backed insights

## Project Structure

```
Crash.ai/
├── agent.py              # LangGraph agent implementation
├── api.py                # FastAPI endpoints
├── tools.py              # Market data tools
├── tasks.py              # Agent skills configuration
├── requirements.txt      # Python dependencies
├── .env                  # API keys (not in git)
├── venv/                 # Virtual environment
└── README.md            # This file
```

## Development

### Adding New Tools

Add tools in `tools.py` using the `@tool` decorator:

```python
@tool
def my_new_tool(param: str):
    """Tool description"""
    # Implementation
    return result
```

### Modifying Analysis Logic

Update system prompts in `agent.py` for different analysis types:
- `TREND_SYSTEM_PROMPT`
- `LOWER_LIMIT_SYSTEM_PROMPT`
- `UPPER_LIMIT_SYSTEM_PROMPT`
- `GENERAL_SYSTEM_PROMPT`

## Notes

- Uses LangGraph for agent workflow (not MCP)
- All tools are called for comprehensive analysis
- Responses are structured for consistency
- API endpoints use GET for predefined queries, POST for custom queries
