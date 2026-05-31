"""
🚀 APIDocForge - AI-Powered API Documentation Auto-Generation Engine

A powerful tool for automatically generating interactive API documentation
from code comments, OpenAPI specifications, and API endpoints.

Author: APIDocForge Team
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "APIDocForge Team"
__email__ = "hello@apidocforge.dev"
__license__ = "MIT"

from apidocforge.core.generator import APIDocGenerator
from apidocforge.core.parser import CodeParser
from apidocforge.models.api import APISpec, Endpoint, Parameter, Response

__all__ = [
    "APIDocGenerator",
    "CodeParser",
    "APISpec",
    "Endpoint",
    "Parameter",
    "Response",
]
