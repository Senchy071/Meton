#!/usr/bin/env python3
"""
Meton HTTP API Server

FastAPI server that provides HTTP endpoints for the VS Code extension
to communicate with the Meton agent.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import Meton components
from cli import MetonCLI
from core.agent import MetonAgent
from core.config import ConfigLoader
from rag.indexer import CodebaseIndexer

# Initialize FastAPI app
app = FastAPI(
    title="Meton API",
    description="HTTP API for Meton AI Assistant",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Meton components
config_loader = ConfigLoader()
agent: Optional[MetonAgent] = None
indexer: Optional[CodebaseIndexer] = None

# Pydantic models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    reasoning: Optional[str] = None

class IndexRequest(BaseModel):
    path: str

class IndexResponse(BaseModel):
    status: str
    files_indexed: int

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]


@app.on_event("startup")
async def startup_event():
    """Initialize Meton agent on startup."""
    global agent, indexer

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        # Initialize agent
        config = config_loader.config
        agent = MetonAgent(config)
        logger.info("Meton agent initialized")

        # Initialize indexer
        indexer = CodebaseIndexer(
            embedding_model_name=config.rag.embedding_model,
            index_path=config.rag.index_path,
            metadata_path=config.rag.metadata_path
        )
        logger.info("Codebase indexer initialized")

    except Exception as e:
        logger.error(f"Failed to initialize Meton: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "agent_initialized": agent is not None,
        "indexer_initialized": indexer is not None
    }


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a query through the Meton agent."""
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Process query through agent
        result = agent.run(request.query)

        return QueryResponse(
            response=result.get("output", ""),
            reasoning=result.get("reasoning", None)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.post("/index", response_model=IndexResponse)
async def index_workspace(request: IndexRequest):
    """Index a codebase directory."""
    if not indexer:
        raise HTTPException(status_code=503, detail="Indexer not initialized")

    try:
        workspace_path = Path(request.path)
        if not workspace_path.exists():
            raise HTTPException(status_code=404, detail="Path not found")

        # Index the directory
        files_indexed = indexer.index_directory(str(workspace_path))

        # Enable RAG in config
        config = config_loader.config
        config.rag.enabled = True
        config.tools.codebase_search.enabled = True
        config_loader.save()

        return IndexResponse(
            status="indexed",
            files_indexed=files_indexed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search_code(request: SearchRequest):
    """Search indexed codebase."""
    if not indexer:
        raise HTTPException(status_code=503, detail="Indexer not initialized")

    try:
        # Search the indexed codebase
        results = indexer.search(request.query, top_k=request.top_k)

        return SearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/status")
async def get_status():
    """Get Meton status information."""
    config = config_loader.config

    return {
        "version": "0.1.0",
        "agent": {
            "initialized": agent is not None,
            "max_iterations": config.agent.max_iterations if agent else None
        },
        "rag": {
            "enabled": config.rag.enabled,
            "indexed_files": indexer.get_stats()["total_chunks"] if indexer else 0
        },
        "tools": {
            "file_ops": config.tools.file_ops.enabled,
            "code_executor": config.tools.code_executor.enabled,
            "web_search": config.tools.web_search.enabled,
            "codebase_search": config.tools.codebase_search.enabled,
            "git_operations": config.tools.git_operations.enabled
        }
    }


def start_server(host: str = "127.0.0.1", port: int = 8000):
    """Start the FastAPI server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Meton HTTP API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")

    args = parser.parse_args()

    print(f"Starting Meton API server on {args.host}:{args.port}")
    start_server(args.host, args.port)
