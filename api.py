from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn

# Import agent functions
from agent import (
    run_trend_analysis,
    run_lower_limit_analysis,
    run_upper_limit_analysis,
    run_general_query
)

# Import cache manager
from cache_manager import get_symbol_data_cached, start_cache_updater, add_symbol_to_cache, get_all_cached_symbols

app = FastAPI(
    title="Market Crash Expert API",
    description="AI Agent API for any symbol crash limit detection and market analysis",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    symbol: str = "GOLDUSD"


class TrendResponse(BaseModel):
    symbol: str
    trend: str
    raw_response: str


class LimitResponse(BaseModel):
    symbol: str
    limit: str
    raw_response: str


class QueryResponse(BaseModel):
    symbol: str
    answer: str


class SymbolDataResponse(BaseModel):
    symbol: str
    trend: str
    lower_limit: str
    upper_limit: str
    timestamp: str
    cache_age_minutes: Optional[int] = None


class AllSymbolsResponse(BaseModel):
    symbols: List[str]
    data: Dict[str, dict]


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "MARKET CRASH EXPERT API",
        "version": "2.0.0",
        "description": "Expert in market trends and strong support/resistance levels for any trading symbol",
        "endpoints": {
            "GET /trend?symbol=GOLDUSD": "Get current market trend for any symbol",
            "GET /lower-limit?symbol=GOLDUSD": "Get strong lower crash limit (support) for any symbol",
            "GET /upper-limit?symbol=GOLDUSD": "Get strong upper crash limit (resistance) for any symbol",
            "GET /getSymbolData?symbol=GOLDUSD": "Get all data (cached) for a specific symbol",
            "GET /getAllSymbols": "Get all cached symbols and their data",
            "POST /addSymbol?symbol=EURUSD": "Add a new symbol to cache tracking",
            "POST /query": "Ask any question about market analysis"
        }
    }


@app.get("/trend", response_model=TrendResponse)
async def get_trend(symbol: str = Query(default="GOLDUSD", description="Trading symbol (e.g., GOLDUSD, EURUSD, BTCUSD)")):
    """
    Get current market trend for any symbol.
    Returns: TREND: bullish | bearish | consolidation
    """
    try:
        result = run_trend_analysis(symbol)
        
        # Extract trend from response
        if "TREND:" in result:
            trend_line = [line for line in result.split('\n') if 'TREND:' in line][0]
            trend = trend_line.split('TREND:')[1].strip().lower()
        else:
            trend = "unknown"
        
        return TrendResponse(
            symbol=symbol,
            trend=trend,
            raw_response=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing trend for {symbol}: {str(e)}")


@app.get("/lower-limit", response_model=LimitResponse)
async def get_lower_limit(symbol: str = Query(default="GOLDUSD", description="Trading symbol (e.g., GOLDUSD, EURUSD, BTCUSD)")):
    """
    Get strong lower crash limit (support level) for any symbol.
    Returns: LIMIT: $XXXX.XX
    """
    try:
        result = run_lower_limit_analysis(symbol)
        
        # Extract limit from response
        if "LIMIT:" in result:
            limit_line = [line for line in result.split('\n') if 'LIMIT:' in line][0]
            limit = limit_line.split('LIMIT:')[1].strip()
        else:
            limit = "N/A"
        
        return LimitResponse(
            symbol=symbol,
            limit=limit,
            raw_response=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing lower limit for {symbol}: {str(e)}")


@app.get("/upper-limit", response_model=LimitResponse)
async def get_upper_limit(symbol: str = Query(default="GOLDUSD", description="Trading symbol (e.g., GOLDUSD, EURUSD, BTCUSD)")):
    """
    Get strong upper crash limit (resistance level) for any symbol.
    Returns: LIMIT: $XXXX.XX
    """
    try:
        result = run_upper_limit_analysis(symbol)
        
        # Extract limit from response
        if "LIMIT:" in result:
            limit_line = [line for line in result.split('\n') if 'LIMIT:' in line][0]
            limit = limit_line.split('LIMIT:')[1].strip()
        else:
            limit = "N/A"
        
        return LimitResponse(
            symbol=symbol,
            limit=limit,
            raw_response=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing upper limit for {symbol}: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def post_query(request: QueryRequest):
    """
    General query endpoint for custom questions about any symbol.
    Accepts POST request with user query and symbol, returns comprehensive answer.
    """
    try:
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = run_general_query(request.query, request.symbol)
        
        return QueryResponse(symbol=request.symbol, answer=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/getSymbolData", response_model=SymbolDataResponse)
async def get_symbol_data(symbol: str = Query(default="GOLDUSD", description="Trading symbol (e.g., GOLDUSD, EURUSD, BTCUSD)")):
    """
    Get all analysis data (trend + limits) for a specific symbol from cache.
    Returns cached data that updates every hour automatically.
    """
    try:
        from datetime import datetime
        
        cache_data = get_symbol_data_cached(symbol)
        
        if not cache_data:
            raise HTTPException(status_code=503, detail=f"Cache data unavailable for {symbol}")
        
        # Calculate cache age
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        age_minutes = int((datetime.now() - cache_time).total_seconds() / 60)
        
        return SymbolDataResponse(
            symbol=symbol,
            trend=cache_data.get('trend', 'unknown'),
            lower_limit=cache_data.get('lower_limit', 'N/A'),
            upper_limit=cache_data.get('upper_limit', 'N/A'),
            timestamp=cache_data['timestamp'],
            cache_age_minutes=age_minutes
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data for {symbol}: {str(e)}")


# Keep backward compatibility with old endpoint
@app.get("/getGoldData", response_model=SymbolDataResponse)
async def get_gold_data():
    """
    Backward compatible endpoint - Get all gold analysis data from cache.
    Use /getSymbolData?symbol=GOLDUSD instead.
    """
    return await get_symbol_data("GOLDUSD")


@app.get("/getAllSymbols", response_model=AllSymbolsResponse)
async def get_all_symbols():
    """
    Get all cached symbols and their data.
    """
    try:
        all_data = get_all_cached_symbols()
        symbols = list(all_data.get('symbols', {}).keys())
        return AllSymbolsResponse(
            symbols=symbols,
            data=all_data.get('symbols', {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all symbols: {str(e)}")


@app.post("/addSymbol")
async def add_symbol(symbol: str = Query(..., description="Trading symbol to add (e.g., EURUSD, BTCUSD)")):
    """
    Add a new symbol to cache tracking.
    The symbol will be automatically updated every hour.
    """
    try:
        result = add_symbol_to_cache(symbol.upper())
        return {"message": f"Symbol {symbol.upper()} added successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding symbol {symbol}: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Market Crash Expert API"}


if __name__ == "__main__":
    print("Starting Market Crash Expert API...")
    print("Available endpoints:")
    print("   GET  /trend?symbol=GOLDUSD        - Get market trend for any symbol")
    print("   GET  /lower-limit?symbol=GOLDUSD  - Get lower crash limit for any symbol")
    print("   GET  /upper-limit?symbol=GOLDUSD  - Get upper crash limit for any symbol")
    print("   GET  /getSymbolData?symbol=GOLDUSD - Get all data (cached) for a symbol")
    print("   GET  /getAllSymbols               - Get all cached symbols")
    print("   POST /addSymbol?symbol=EURUSD     - Add new symbol to tracking")
    print("   POST /query                       - Ask custom questions")
    print("\n🕐 Starting hourly cache updater...")
    start_cache_updater()
    print("\n🌐 Server running on http://localhost:8000")
    print("📖 API docs available at http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
