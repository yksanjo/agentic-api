"""
Agentic API - REST API Server for Agentic Scraper

A FastAPI-based REST API that exposes the agentic scraper functionality:
- POST /scrape - Scrape a URL with a goal
- POST /scrape/batch - Batch scrape multiple URLs
- GET /tools - List available tools
- POST /tools/execute - Execute a specific tool
- GET /memory - Get memory statistics
- POST /memory - Add to memory
- GET /status - Get agent status
"""

import asyncio
import json
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn


# Import from agentic-scraper (assuming it's in parent directory)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "agentic-scraper"))

try:
    from agent import AgenticScraperAgent
    from tools import ToolExecutor
    from memory import LearningEngine, SessionMemory
except ImportError:
    # Fallback if not available
    AgenticScraperAgent = None
    ToolExecutor = None
    LearningEngine = None
    SessionMemory = None


app = FastAPI(
    title="Agentic API",
    description="REST API for intelligent web scraping agent",
    version="1.0.0"
)


# Global state
agent: Optional[AgenticScraperAgent] = None
tool_executor: Optional[ToolExecutor] = None
learning_engine = None
session_memory = None
scrape_history = []


# Request/Response Models
class ScrapeRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")
    goal: str = Field(..., description="What to extract")
    use_browser: bool = Field(False, description="Use real browser (requires Playwright)")


class ScrapeResponse(BaseModel):
    success: bool
    data: dict
    url: str
    goal: str
    actions_taken: int
    timestamp: str


class BatchScrapeRequest(BaseModel):
    targets: list[ScrapeRequest] = Field(..., description="List of URLs to scrape")


class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(..., description="Name of tool to execute")
    params: dict = Field(default_factory=dict, description="Tool parameters")


class ToolResponse(BaseModel):
    success: bool
    result: dict


class MemoryRequest(BaseModel):
    url: str
    selector: str
    success: bool
    element_type: Optional[str] = None


class StatusResponse(BaseModel):
    agent_status: dict
    memory_stats: dict
    session_summary: dict
    history_count: int


# Initialize components
def initialize_components():
    global agent, tool_executor, learning_engine, session_memory
    
    if AgenticScraperAgent:
        agent = AgenticScraperAgent()
    
    if ToolExecutor:
        tool_executor = ToolExecutor()
    
    if LearningEngine:
        learning_engine = LearningEngine()
    
    if SessionMemory:
        session_memory = SessionMemory()


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    initialize_components()
    print("🤖 Agentic API started")


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Agentic API",
        "version": "1.0.0",
        "description": "REST API for intelligent web scraping agent",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape(request: ScrapeRequest):
    """Scrape a URL with a goal"""
    
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Run scrape
        result = await agent.scrape(request.url, request.goal)
        
        # Add to history
        scrape_history.append({
            "url": request.url,
            "goal": request.goal,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 100
        if len(scrape_history) > 100:
            scrape_history.pop(0)
        
        # Learn from result
        if learning_engine:
            learning_engine.learn_from_extraction(request.url, result)
        
        return ScrapeResponse(
            success=result.get("success", False),
            data=result,
            url=request.url,
            goal=request.goal,
            actions_taken=result.get("actions_taken", 0),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape/batch")
async def batch_scrape(request: BatchScrapeRequest):
    """Batch scrape multiple URLs"""
    
    results = []
    
    for target in request.targets:
        if agent:
            result = await agent.scrape(target.url, target.goal)
            results.append({
                "url": target.url,
                "goal": target.goal,
                "result": result
            })
    
    return {
        "success": True,
        "total": len(request.targets),
        "completed": len(results),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/tools")
async def list_tools():
    """List all available tools"""
    
    if not tool_executor:
        return {"tools": [], "message": "Tool executor not initialized"}
    
    tools = tool_executor.registry.list_tools()
    
    # Get tool schemas
    schemas = tool_executor.registry.get_all_schemas()
    
    return {
        "tools": tools,
        "count": len(tools),
        "schemas": schemas
    }


@app.post("/tools/execute", response_model=ToolResponse)
async def execute_tool(request: ToolExecuteRequest):
    """Execute a specific tool"""
    
    if not tool_executor:
        raise HTTPException(status_code=503, detail="Tool executor not initialized")
    
    try:
        result = await tool_executor.execute(request.tool_name, request.params)
        
        return ToolResponse(
            success=result.get("success", False),
            result=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory")
async def get_memory():
    """Get memory statistics"""
    
    if not learning_engine:
        return {"stats": {}, "message": "Learning engine not initialized"}
    
    stats = learning_engine.get_statistics()
    
    return {
        "stats": stats,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/memory")
async def add_memory(request: MemoryRequest):
    """Add to memory"""
    
    if not learning_engine:
        raise HTTPException(status_code=503, detail="Learning engine not initialized")
    
    learning_engine.remember_selector(
        url=request.url,
        selector=request.selector,
        success=request.success,
        element_type=request.element_type
    )
    
    return {
        "success": True,
        "message": "Memory added",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/memory/recommendations")
async def get_recommendations(url: str):
    """Get memory recommendations for a URL"""
    
    if not learning_engine:
        raise HTTPException(status_code=503, detail="Learning engine not initialized")
    
    recommendations = learning_engine.get_recommendations(url)
    
    return recommendations


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get agent status"""
    
    agent_status = agent.get_status() if agent else {}
    memory_stats = learning_engine.get_statistics() if learning_engine else {}
    session_summary = session_memory.summarize() if session_memory else {}
    
    return StatusResponse(
        agent_status=agent_status,
        memory_stats=memory_stats,
        session_summary=session_summary,
        history_count=len(scrape_history)
    )


@app.get("/history")
async def get_history(limit: int = 10):
    """Get scrape history"""
    
    return {
        "history": scrape_history[-limit:],
        "total": len(scrape_history)
    }


# Run server
def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
