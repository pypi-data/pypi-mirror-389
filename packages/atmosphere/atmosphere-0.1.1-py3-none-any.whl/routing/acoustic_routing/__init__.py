"""
Acoustic Routing - Spatial Audio and Network Routing System

This package provides tools for modeling acoustic routing through network topologies,
with applications in spatial audio processing and network analysis.

Subpackages:
    core: Core routing and audio processing functionality
    api: Web API and visualization endpoints
    models: Data models and type definitions
"""

__version__ = "0.1.0"

# Import core functionality
from .core.network import AcousticRoutingNetwork  # noqa: F401
from .core.visualization import visualize_network  # noqa: F401
