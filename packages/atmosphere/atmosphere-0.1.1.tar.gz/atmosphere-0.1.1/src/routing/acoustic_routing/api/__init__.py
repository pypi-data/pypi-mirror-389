"""
API module for the Acoustic Routing system.

This package provides web API endpoints for interacting with
the acoustic routing system.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Acoustic Routing API",
    description="API for acoustic routing and network analysis",
    version="0.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from . import routes  # noqa: F401
