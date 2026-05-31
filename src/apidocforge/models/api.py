"""API specification data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class HTTPMethod(Enum):
    """HTTP methods supported by APIDocForge."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ParameterLocation(Enum):
    """Parameter location in HTTP request."""
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    COOKIE = "cookie"
    BODY = "body"


@dataclass
class Schema:
    """Data schema definition."""
    type: str
    format: Optional[str] = None
    description: Optional[str] = None
    default: Any = None
    enum: Optional[List[Any]] = None
    items: Optional[Schema] = None
    properties: Dict[str, Schema] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    example: Any = None
    nullable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary."""
        result = {"type": self.type}
        if self.format:
            result["format"] = self.format
        if self.description:
            result["description"] = self.description
        if self.default is not None:
            result["default"] = self.default
        if self.enum:
            result["enum"] = self.enum
        if self.items:
            result["items"] = self.items.to_dict()
        if self.properties:
            result["properties"] = {k: v.to_dict() for k, v in self.properties.items()}
        if self.required:
            result["required"] = self.required
        if self.example is not None:
            result["example"] = self.example
        if self.nullable:
            result["nullable"] = True
        return result


@dataclass
class Parameter:
    """API endpoint parameter."""
    name: str
    location: ParameterLocation
    schema: Schema
    description: Optional[str] = None
    required: bool = False
    deprecated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameter to dictionary."""
        result = {
            "name": self.name,
            "in": self.location.value,
            "schema": self.schema.to_dict(),
            "required": self.required,
        }
        if self.description:
            result["description"] = self.description
        if self.deprecated:
            result["deprecated"] = True
        return result


@dataclass
class Response:
    """API endpoint response."""
    status_code: str
    description: str
    schema: Optional[Schema] = None
    headers: Dict[str, Schema] = field(default_factory=dict)
    content_type: str = "application/json"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        result = {
            "description": self.description,
        }
        if self.schema:
            result["content"] = {
                self.content_type: {
                    "schema": self.schema.to_dict()
                }
            }
        if self.headers:
            result["headers"] = {k: v.to_dict() for k, v in self.headers.items()}
        return result


@dataclass
class Endpoint:
    """API endpoint definition."""
    path: str
    method: HTTPMethod
    summary: Optional[str] = None
    description: Optional[str] = None
    operation_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[Schema] = None
    responses: Dict[str, Response] = field(default_factory=dict)
    deprecated: bool = False
    security: List[Dict[str, List[str]]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert endpoint to dictionary."""
        result: Dict[str, Any] = {}
        if self.summary:
            result["summary"] = self.summary
        if self.description:
            result["description"] = self.description
        if self.operation_id:
            result["operationId"] = self.operation_id
        if self.tags:
            result["tags"] = self.tags
        if self.parameters:
            result["parameters"] = [p.to_dict() for p in self.parameters]
        if self.request_body:
            result["requestBody"] = {
                "content": {
                    "application/json": {
                        "schema": self.request_body.to_dict()
                    }
                }
            }
        if self.responses:
            result["responses"] = {k: v.to_dict() for k, v in self.responses.items()}
        if self.deprecated:
            result["deprecated"] = True
        if self.security:
            result["security"] = self.security
        return result


@dataclass
class Server:
    """API server definition."""
    url: str
    description: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert server to dictionary."""
        result = {"url": self.url}
        if self.description:
            result["description"] = self.description
        if self.variables:
            result["variables"] = self.variables
        return result


@dataclass
class Tag:
    """API tag definition."""
    name: str
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tag to dictionary."""
        result = {"name": self.name}
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class APISpec:
    """Complete API specification."""
    title: str
    version: str
    description: Optional[str] = None
    terms_of_service: Optional[str] = None
    contact: Optional[Dict[str, str]] = None
    license: Optional[Dict[str, str]] = None
    servers: List[Server] = field(default_factory=list)
    endpoints: List[Endpoint] = field(default_factory=list)
    tags: List[Tag] = field(default_factory=list)
    schemas: Dict[str, Schema] = field(default_factory=dict)
    security_schemes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_openapi(self) -> Dict[str, Any]:
        """Convert to OpenAPI 3.0 specification."""
        spec: Dict[str, Any] = {
            "openapi": "3.0.3",
            "info": {
                "title": self.title,
                "version": self.version,
            },
        }
        
        if self.description:
            spec["info"]["description"] = self.description
        if self.terms_of_service:
            spec["info"]["termsOfService"] = self.terms_of_service
        if self.contact:
            spec["info"]["contact"] = self.contact
        if self.license:
            spec["info"]["license"] = self.license
        
        if self.servers:
            spec["servers"] = [s.to_dict() for s in self.servers]
        
        if self.tags:
            spec["tags"] = [t.to_dict() for t in self.tags]
        
        # Group endpoints by path
        paths: Dict[str, Dict[str, Any]] = {}
        for endpoint in self.endpoints:
            if endpoint.path not in paths:
                paths[endpoint.path] = {}
            paths[endpoint.path][endpoint.method.value.lower()] = endpoint.to_dict()
        spec["paths"] = paths
        
        # Components
        components: Dict[str, Any] = {}
        if self.schemas:
            components["schemas"] = {k: v.to_dict() for k, v in self.schemas.items()}
        if self.security_schemes:
            components["securitySchemes"] = self.security_schemes
        if components:
            spec["components"] = components
        
        return spec
    
    def get_endpoints_by_tag(self, tag: str) -> List[Endpoint]:
        """Get all endpoints with a specific tag."""
        return [e for e in self.endpoints if tag in e.tags]
    
    def get_endpoints_by_path(self, path: str) -> List[Endpoint]:
        """Get all endpoints for a specific path."""
        return [e for e in self.endpoints if e.path == path]
