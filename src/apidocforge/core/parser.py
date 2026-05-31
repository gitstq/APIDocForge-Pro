"""Code parser for extracting API documentation from source files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from apidocforge.models.api import (
    APISpec,
    Endpoint,
    HTTPMethod,
    Parameter,
    ParameterLocation,
    Response,
    Schema,
    Server,
    Tag,
)
from apidocforge.models.config import Config, ParserType


class CodeParser:
    """Parser for extracting API documentation from source code."""
    
    # URL pattern for extracting route information
    ROUTE_PATTERNS = {
        "python": {
            "decorator": r'@(?:app|router|blueprint|api)\.route\s*\(\s*["\']([^"\']+)["\']',
            "fastapi": r'@(?:app|router)\.(get|post|put|delete|patch|head|options)\s*\(\s*["\']([^"\']+)["\']',
            "flask": r'@(?:app|blueprint)\.(route)\s*\(\s*["\']([^"\']+)["\'][^)]*methods\s*=\s*\[([^\]]+)\]',
            "django": r'path\s*\(\s*["\']([^"\']+)["\']\s*,\s*([^,)]+)',
            "docstring": r'"""([\s\S]*?)"""',
        },
        "javascript": {
            "express": r'(?:app|router)\.(get|post|put|delete|patch|head|options)\s*\(\s*["\']([^"\']+)["\']',
            "jsdoc": r'/\*\*([\s\S]*?)\*/',
        },
        "typescript": {
            "decorator": r'@(?:Get|Post|Put|Delete|Patch|Head|Options)\s*\(\s*["\']([^"\']+)["\']',
            "jsdoc": r'/\*\*([\s\S]*?)\*/',
        },
        "go": {
            "handler": r'func\s+\w+.*http\.ResponseWriter.*\*http\.Request',
            "comment": r'//\s*(.+)',
        },
        "java": {
            "spring": r'@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(\s*["\']?([^"\')]+)',
            "javadoc": r'/\*\*([\s\S]*?)\*/',
        },
        "rust": {
            "actix": r'#\[(?:get|post|put|delete|patch|head|options)\s*\(\s*"([^"]+)"',
            "doc": r'///\s*(.+)',
        },
    }
    
    def __init__(self, config: Config) -> None:
        """Initialize parser with configuration."""
        self.config = config
    
    def detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension."""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".mjs": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".java": "java",
            ".rs": "rust",
        }
        return extension_map.get(file_path.suffix.lower())
    
    def parse_file(self, file_path: Path) -> List[Endpoint]:
        """Parse a single file and extract API endpoints."""
        language = self.detect_language(file_path)
        if not language:
            return []
        
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return []
        
        endpoints = []
        
        if language == "python":
            endpoints = self._parse_python(content, file_path)
        elif language == "javascript":
            endpoints = self._parse_javascript(content, file_path)
        elif language == "typescript":
            endpoints = self._parse_typescript(content, file_path)
        elif language == "go":
            endpoints = self._parse_go(content, file_path)
        elif language == "java":
            endpoints = self._parse_java(content, file_path)
        elif language == "rust":
            endpoints = self._parse_rust(content, file_path)
        
        return endpoints
    
    def _parse_python(self, content: str, file_path: Path) -> List[Endpoint]:
        """Parse Python code for API endpoints."""
        endpoints = []
        
        # FastAPI/Flask route patterns
        patterns = [
            # FastAPI: @app.get("/path")
            (r'@(?:app|router)\.(get|post|put|delete|patch|head|options)\s*\(\s*["\']([^"\']+)["\']', "fastapi"),
            # Flask: @app.route("/path", methods=["GET"])
            (r'@(?:app|blueprint)\.route\s*\(\s*["\']([^"\']+)["\'][^)]*methods\s*=\s*\[([^\]]+)\]', "flask"),
            # Flask default GET: @app.route("/path")
            (r'@(?:app|blueprint)\.route\s*\(\s*["\']([^"\']+)["\']\s*\)(?!.*methods)', "flask_get"),
        ]
        
        for pattern, framework in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                if framework == "fastapi":
                    method = match.group(1).upper()
                    path = match.group(2)
                elif framework == "flask":
                    path = match.group(1)
                    methods_str = match.group(2)
                    method = methods_str.replace('"', "").replace("'", "").split(",")[0].strip().upper()
                else:  # flask_get
                    path = match.group(1)
                    method = "GET"
                
                # Extract docstring
                func_start = match.end()
                docstring = self._extract_python_docstring(content, func_start)
                
                endpoint = self._create_endpoint_from_docstring(
                    path=path,
                    method=HTTPMethod(method),
                    docstring=docstring,
                    language="python"
                )
                endpoints.append(endpoint)
        
        return endpoints
    
    def _parse_javascript(self, content: str, file_path: Path) -> List[Endpoint]:
        """Parse JavaScript code for API endpoints."""
        endpoints = []
        
        # Express.js patterns
        pattern = r'(?:app|router)\.(get|post|put|delete|patch|head|options)\s*\(\s*["\']([^"\']+)["\']'
        
        for match in re.finditer(pattern, content, re.IGNORECASE):
            method = match.group(1).upper()
            path = match.group(2)
            
            # Extract JSDoc
            func_start = match.end()
            jsdoc = self._extract_jsdoc(content[:match.start()])
            
            endpoint = self._create_endpoint_from_docstring(
                path=path,
                method=HTTPMethod(method),
                docstring=jsdoc,
                language="javascript"
            )
            endpoints.append(endpoint)
        
        return endpoints
    
    def _parse_typescript(self, content: str, file_path: Path) -> List[Endpoint]:
        """Parse TypeScript code for API endpoints."""
        endpoints = []
        
        # NestJS/TS decorators
        patterns = [
            (r'@(?:Get|Post|Put|Delete|Patch|Head|Options)\s*\(\s*["\']([^"\']+)["\']', "nestjs"),
        ]
        
        method_map = {
            "Get": "GET",
            "Post": "POST",
            "Put": "PUT",
            "Delete": "DELETE",
            "Patch": "PATCH",
            "Head": "HEAD",
            "Options": "OPTIONS",
        }
        
        for pattern, framework in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                decorator = match.group(0)
                path = match.group(1)
                
                # Extract method from decorator name
                for key, value in method_map.items():
                    if key in decorator:
                        method = value
                        break
                else:
                    method = "GET"
                
                # Extract JSDoc
                jsdoc = self._extract_jsdoc(content[:match.start()])
                
                endpoint = self._create_endpoint_from_docstring(
                    path=path,
                    method=HTTPMethod(method),
                    docstring=jsdoc,
                    language="typescript"
                )
                endpoints.append(endpoint)
        
        return endpoints
    
    def _parse_go(self, content: str, file_path: Path) -> List[Endpoint]:
        """Parse Go code for API endpoints."""
        endpoints = []
        
        # Look for http.HandleFunc patterns
        pattern = r'http\.HandleFunc\s*\(\s*["\']([^"\']+)["\']'
        
        for match in re.finditer(pattern, content):
            path = match.group(1)
            
            # Extract comments before this line
            line_start = content[:match.start()].rfind("\n")
            comments = self._extract_go_comments(content, line_start)
            
            # Default to GET for simplicity
            endpoint = self._create_endpoint_from_docstring(
                path=path,
                method=HTTPMethod.GET,
                docstring=comments,
                language="go"
            )
            endpoints.append(endpoint)
        
        return endpoints
    
    def _parse_java(self, content: str, file_path: Path) -> List[Endpoint]:
        """Parse Java code for API endpoints."""
        endpoints = []
        
        # Spring annotations
        pattern = r'@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(\s*["\']?([^"\')]+)'
        
        method_map = {
            "GetMapping": "GET",
            "PostMapping": "POST",
            "PutMapping": "PUT",
            "DeleteMapping": "DELETE",
            "PatchMapping": "PATCH",
            "RequestMapping": "GET",
        }
        
        for match in re.finditer(pattern, content):
            annotation = match.group(0)
            path = match.group(1).replace('"', "").strip()
            
            # Determine method
            method = "GET"
            for key, value in method_map.items():
                if key in annotation:
                    method = value
                    break
            
            # Extract Javadoc
            javadoc = self._extract_javadoc(content[:match.start()])
            
            endpoint = self._create_endpoint_from_docstring(
                path=path,
                method=HTTPMethod(method),
                docstring=javadoc,
                language="java"
            )
            endpoints.append(endpoint)
        
        return endpoints
    
    def _parse_rust(self, content: str, file_path: Path) -> List[Endpoint]:
        """Parse Rust code for API endpoints."""
        endpoints = []
        
        # Actix-web route attributes
        pattern = r'#\[(?:get|post|put|delete|patch|head|options)\s*\(\s*"([^"]+)"'
        
        for match in re.finditer(pattern, content, re.IGNORECASE):
            method = match.group(0).split("[")[1].split("(")[0].strip().upper()
            path = match.group(1)
            
            # Extract doc comments
            docs = self._extract_rust_docs(content, match.start())
            
            endpoint = self._create_endpoint_from_docstring(
                path=path,
                method=HTTPMethod(method),
                docstring=docs,
                language="rust"
            )
            endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_python_docstring(self, content: str, start_pos: int) -> str:
        """Extract Python docstring after a given position."""
        # Find the function definition
        func_match = re.search(r'def\s+\w+', content[start_pos:])
        if not func_match:
            return ""
        
        func_start = start_pos + func_match.end()
        
        # Look for triple-quoted docstring
        docstring_match = re.search(
            r'\s*(?:\([^)]*\)\s*(?:->\s*[^:]+:)?\s*:\s*)?[r]?["\']{3}([\s\S]*?)["\']{3}',
            content[func_start:func_start + 2000]
        )
        
        if docstring_match:
            return docstring_match.group(1).strip()
        return ""
    
    def _extract_jsdoc(self, content: str) -> str:
        """Extract JSDoc comment before a given position."""
        # Find the last JSDoc comment
        matches = list(re.finditer(r'/\*\*([\s\S]*?)\*/', content))
        if matches:
            return matches[-1].group(1).strip()
        return ""
    
    def _extract_javadoc(self, content: str) -> str:
        """Extract Javadoc comment."""
        matches = list(re.finditer(r'/\*\*([\s\S]*?)\*/', content))
        if matches:
            return matches[-1].group(1).strip()
        return ""
    
    def _extract_go_comments(self, content: str, line_start: int) -> str:
        """Extract Go comments before a line."""
        lines = content[:line_start].split("\n")
        comments = []
        for line in reversed(lines):
            stripped = line.strip()
            if stripped.startswith("//"):
                comments.insert(0, stripped[2:].strip())
            elif stripped:
                break
        return "\n".join(comments)
    
    def _extract_rust_docs(self, content: str, pos: int) -> str:
        """Extract Rust doc comments."""
        lines = content[:pos].split("\n")
        docs = []
        for line in reversed(lines):
            stripped = line.strip()
            if stripped.startswith("///"):
                docs.insert(0, stripped[3:].strip())
            elif stripped.startswith("//!"):
                docs.insert(0, stripped[3:].strip())
            elif stripped:
                break
        return "\n".join(docs)
    
    def _create_endpoint_from_docstring(
        self,
        path: str,
        method: HTTPMethod,
        docstring: str,
        language: str
    ) -> Endpoint:
        """Create an Endpoint from extracted docstring."""
        # Parse docstring for description and parameters
        lines = docstring.split("\n") if docstring else []
        
        summary = ""
        description = ""
        params = []
        responses = {}
        tags = []
        
        if lines:
            # First non-empty line is summary
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith(("@", ":param", ":return", "@param", "@return")):
                    summary = stripped
                    break
            
            # Rest is description
            desc_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith(("@", ":param", ":return", "@param", "@return", "Args:", "Returns:")):
                    desc_lines.append(stripped)
            description = " ".join(desc_lines[1:]) if len(desc_lines) > 1 else ""
            
            # Extract parameters
            param_patterns = [
                r'@param\s+(\w+)\s*(?:\{([^}]+)\})?\s*(.+)',
                r':param\s+(\w+):\s*(.+)',
                r'@param\s+(\w+)\s+(.+)',
            ]
            for line in lines:
                for pattern in param_patterns:
                    match = re.search(pattern, line)
                    if match:
                        if len(match.groups()) == 3:
                            param_name = match.group(1)
                            param_type = match.group(2) or "string"
                            param_desc = match.group(3)
                        else:
                            param_name = match.group(1)
                            param_type = "string"
                            param_desc = match.group(2)
                        
                        param = Parameter(
                            name=param_name,
                            location=ParameterLocation.QUERY,
                            schema=Schema(type=param_type.lower()),
                            description=param_desc,
                        )
                        params.append(param)
                        break
        
        # Create default 200 response
        responses["200"] = Response(
            status_code="200",
            description="Successful response",
            schema=Schema(type="object")
        )
        
        return Endpoint(
            path=path,
            method=method,
            summary=summary or f"{method.value} {path}",
            description=description,
            operation_id=f"{method.value.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '')}",
            tags=tags or ["Default"],
            parameters=params,
            responses=responses,
        )
    
    def parse_openapi(self, file_path: Path) -> Optional[APISpec]:
        """Parse an existing OpenAPI/Swagger specification file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            
            if file_path.suffix in (".yaml", ".yml"):
                spec = yaml.safe_load(content)
            else:
                spec = json.loads(content)
            
            return self._convert_openapi_to_spec(spec)
        except Exception:
            return None
    
    def _convert_openapi_to_spec(self, openapi: Dict[str, Any]) -> APISpec:
        """Convert OpenAPI dict to APISpec model."""
        info = openapi.get("info", {})
        
        # Parse endpoints
        endpoints = []
        paths = openapi.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ("parameters", "servers"):
                    continue
                
                endpoint = Endpoint(
                    path=path,
                    method=HTTPMethod(method.upper()),
                    summary=details.get("summary"),
                    description=details.get("description"),
                    operation_id=details.get("operationId"),
                    tags=details.get("tags", []),
                )
                endpoints.append(endpoint)
        
        # Parse servers
        servers = []
        for server in openapi.get("servers", []):
            servers.append(Server(
                url=server.get("url", ""),
                description=server.get("description"),
            ))
        
        return APISpec(
            title=info.get("title", "API"),
            version=info.get("version", "1.0.0"),
            description=info.get("description"),
            servers=servers,
            endpoints=endpoints,
        )
    
    def parse_directory(self, directory: Path) -> APISpec:
        """Parse all files in a directory and create API specification."""
        all_endpoints = []
        
        for pattern in self.config.include_patterns:
            for file_path in directory.rglob(pattern):
                # Check exclude patterns
                excluded = False
                for exclude in self.config.exclude_patterns:
                    if file_path.match(exclude):
                        excluded = True
                        break
                
                if not excluded:
                    endpoints = self.parse_file(file_path)
                    all_endpoints.extend(endpoints)
        
        # Also check for existing OpenAPI files
        for openapi_file in directory.rglob("*openapi*.json"):
            spec = self.parse_openapi(openapi_file)
            if spec:
                return spec
        
        for openapi_file in directory.rglob("*swagger*.json"):
            spec = self.parse_openapi(openapi_file)
            if spec:
                return spec
        
        for openapi_file in directory.rglob("*openapi*.yaml"):
            spec = self.parse_openapi(openapi_file)
            if spec:
                return spec
        
        # Create spec from parsed endpoints
        return APISpec(
            title=self.config.title,
            version=self.config.version,
            description=self.config.description or f"API documentation generated from {directory.name}",
            endpoints=all_endpoints,
            servers=[Server(url=self.config.base_url or "/")] if self.config.base_url else [],
        )
