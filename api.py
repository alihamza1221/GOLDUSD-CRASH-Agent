from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

# Import agent functions
from agent import (
    run_trend_analysis,
    run_lower_limit_analysis,
    run_upper_limit_analysis,
    run_general_query
)

app = FastAPI(
    title="Gold Crash Expert API",
    description="AI Agent API for GOLDUSD crash limit detection and market analysis",
    version="1.0.0"
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


class TrendResponse(BaseModel):
    trend: str
    raw_response: str


class LimitResponse(BaseModel):
    limit: str
    raw_response: str


class QueryResponse(BaseModel):
    answer: str


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "GOLDUSD CRASH EXPERT API",
        "version": "1.0.0",
        "description": "Expert in market trends and strong support/resistance levels",
        "endpoints": {
            "GET /trend": "Get current gold market trend for this week",
            "GET /lower-limit": "Get strong lower crash limit (support) for this week",
            "GET /upper-limit": "Get strong upper crash limit (resistance) for this week",
            "POST /query": "Ask any question about gold market analysis"
        }
    }


@app.get("/trend", response_model=TrendResponse)
async def get_trend():
    """
    Endpoint 1: Get current gold market trend for this week.
    Returns: TREND: bullish | bearish | consolidation
    """
    try:
        result = run_trend_analysis()
        
        # Extract trend from response
        if "TREND:" in result:
            trend_line = [line for line in result.split('\n') if 'TREND:' in line][0]
            trend = trend_line.split('TREND:')[1].strip().lower()
        else:
            trend = "unknown"
        
        return TrendResponse(
            trend=trend,
            raw_response=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing trend: {str(e)}")


@app.get("/lower-limit", response_model=LimitResponse)
async def get_lower_limit():
    """
    Endpoint 2: Get strong lower crash limit (support level) for this week.
    Returns: LIMIT: $XXXX.XX
    """
    try:
        result = run_lower_limit_analysis()
        
        # Extract limit from response
        if "LIMIT:" in result:
            limit_line = [line for line in result.split('\n') if 'LIMIT:' in line][0]
            limit = limit_line.split('LIMIT:')[1].strip()
        else:
            limit = "N/A"
        
        return LimitResponse(
            limit=limit,
            raw_response=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing lower limit: {str(e)}")


@app.get("/upper-limit", response_model=LimitResponse)
async def get_upper_limit():
    """
    Endpoint 3: Get strong upper crash limit (resistance level) for this week.
    Returns: LIMIT: $XXXX.XX
    """
    try:
        result = run_upper_limit_analysis()
        
        # Extract limit from response
        if "LIMIT:" in result:
            limit_line = [line for line in result.split('\n') if 'LIMIT:' in line][0]
            limit = limit_line.split('LIMIT:')[1].strip()
        else:
            limit = "N/A"
        
        return LimitResponse(
            limit=limit,
            raw_response=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing upper limit: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def post_query(request: QueryRequest):
    """
    Endpoint 4: General query endpoint for custom questions.
    Accepts POST request with user query and returns comprehensive answer.
    """
    try:
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = run_general_query(request.query)
        
        return QueryResponse(answer=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Gold Crash Expert API"}


if __name__ == "__main__":
    print("🚀 Starting Gold Crash Expert API...")
    print("📊 Available endpoints:")
    print("   GET  /trend        - Get market trend")
    print("   GET  /lower-limit  - Get lower crash limit")
    print("   GET  /upper-limit  - Get upper crash limit")
    print("   POST /query        - Ask custom questions")
    print("\n🌐 Server running on http://localhost:8000")
    print("📖 API docs available at http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
