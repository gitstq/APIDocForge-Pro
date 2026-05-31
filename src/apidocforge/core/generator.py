"""Documentation generator for APIDocForge."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape

from apidocforge.models.api import APISpec, Endpoint, Server
from apidocforge.models.config import Config, OutputFormat


class APIDocGenerator:
    """Generator for API documentation in various formats."""
    
    def __init__(self, config: Config) -> None:
        """Initialize generator with configuration."""
        self.config = config
        self.template_dir = Path(__file__).parent.parent / "templates"
        
        # Setup Jinja2 environment
        if self.template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=select_autoescape(["html", "xml"]),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self.jinja_env = Environment(
                loader=PackageLoader("apidocforge", "templates"),
                autoescape=select_autoescape(["html", "xml"]),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        
        # Add custom filters
        self.jinja_env.filters["tojson"] = lambda x: json.dumps(x, ensure_ascii=False)
    
    def generate(self, spec: APISpec) -> Dict[str, Path]:
        """Generate documentation in all configured formats."""
        output_files = {}
        
        # Ensure output directory exists
        self.config.output_path.mkdir(parents=True, exist_ok=True)
        
        for fmt in self.config.output_formats:
            if fmt == OutputFormat.HTML:
                output_files["html"] = self._generate_html(spec)
            elif fmt == OutputFormat.MARKDOWN:
                output_files["markdown"] = self._generate_markdown(spec)
            elif fmt == OutputFormat.OPENAPI:
                output_files["openapi_json"] = self._generate_openapi_json(spec)
                output_files["openapi_yaml"] = self._generate_openapi_yaml(spec)
            elif fmt == OutputFormat.JSON:
                output_files["json"] = self._generate_json(spec)
            elif fmt == OutputFormat.YAML:
                output_files["yaml"] = self._generate_yaml(spec)
        
        return output_files
    
    def _generate_html(self, spec: APISpec) -> Path:
        """Generate interactive HTML documentation."""
        output_dir = self.config.output_path / "html"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate index.html
        template = self._get_html_template()
        
        html_content = template.render(
            spec=spec,
            title=spec.title,
            version=spec.version,
            description=spec.description,
            endpoints=spec.endpoints,
            servers=spec.servers,
            enable_try_it=self.config.enable_try_it,
            enable_search=self.config.enable_search,
            theme=self.config.theme,
        )
        
        output_file = output_dir / "index.html"
        output_file.write_text(html_content, encoding="utf-8")
        
        # Copy static assets
        self._copy_static_assets(output_dir)
        
        return output_file
    
    def _get_html_template(self) -> Any:
        """Get the HTML template."""
        try:
            return self.jinja_env.get_template("docs.html")
        except:
            # Use built-in template
            return self.jinja_env.from_string(self._get_default_html_template())
    
    def _get_default_html_template(self) -> str:
        """Get the default HTML template."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - API Documentation</title>
    <style>
        :root {
            --primary: #3b82f6;
            --primary-dark: #2563eb;
            --secondary: #64748b;
            --background: #f8fafc;
            --surface: #ffffff;
            --text: #1e293b;
            --text-light: #64748b;
            --border: #e2e8f0;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --get: #10b981;
            --post: #3b82f6;
            --put: #f59e0b;
            --delete: #ef4444;
            --patch: #8b5cf6;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--background);
            color: var(--text);
            line-height: 1.6;
        }
        
        .header {
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 1.5rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
        }
        
        .version {
            background: var(--primary);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 2rem;
            padding: 2rem;
        }
        
        .sidebar {
            position: sticky;
            top: 100px;
            height: calc(100vh - 120px);
            overflow-y: auto;
        }
        
        .search-box {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            font-size: 0.875rem;
            margin-bottom: 1rem;
        }
        
        .search-box:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .nav-section {
            margin-bottom: 1.5rem;
        }
        
        .nav-title {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-light);
            margin-bottom: 0.5rem;
            padding: 0 0.5rem;
        }
        
        .nav-item {
            display: block;
            padding: 0.5rem;
            color: var(--text);
            text-decoration: none;
            border-radius: 0.375rem;
            font-size: 0.875rem;
            transition: background 0.2s;
        }
        
        .nav-item:hover {
            background: var(--background);
        }
        
        .main-content {
            min-width: 0;
        }
        
        .hero {
            background: var(--surface);
            border-radius: 1rem;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid var(--border);
        }
        
        .hero h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .hero p {
            color: var(--text-light);
            font-size: 1.125rem;
        }
        
        .server-url {
            background: #1e293b;
            color: #e2e8f0;
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.875rem;
            margin-top: 1rem;
        }
        
        .endpoint {
            background: var(--surface);
            border-radius: 1rem;
            border: 1px solid var(--border);
            margin-bottom: 1.5rem;
            overflow: hidden;
        }
        
        .endpoint-header {
            padding: 1.25rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 1rem;
            cursor: pointer;
        }
        
        .method {
            padding: 0.375rem 0.75rem;
            border-radius: 0.375rem;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            color: white;
        }
        
        .method.get { background: var(--get); }
        .method.post { background: var(--post); }
        .method.put { background: var(--put); }
        .method.delete { background: var(--delete); }
        .method.patch { background: var(--patch); }
        
        .path {
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9375rem;
            font-weight: 500;
        }
        
        .endpoint-summary {
            color: var(--text-light);
            font-size: 0.875rem;
            margin-left: auto;
        }
        
        .endpoint-body {
            padding: 1.5rem;
        }
        
        .section-title {
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            color: var(--text);
        }
        
        .description {
            color: var(--text-light);
            margin-bottom: 1.5rem;
            line-height: 1.7;
        }
        
        .params-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1.5rem;
        }
        
        .params-table th,
        .params-table td {
            text-align: left;
            padding: 0.75rem;
            border-bottom: 1px solid var(--border);
        }
        
        .params-table th {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-light);
        }
        
        .param-name {
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.875rem;
            color: var(--primary);
        }
        
        .param-type {
            font-size: 0.75rem;
            color: var(--text-light);
            background: var(--background);
            padding: 0.125rem 0.375rem;
            border-radius: 0.25rem;
        }
        
        .param-required {
            font-size: 0.75rem;
            color: var(--error);
        }
        
        .code-block {
            background: #1e293b;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 0.5rem;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.875rem;
            overflow-x: auto;
            margin-bottom: 1rem;
        }
        
        .try-it-btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.625rem 1.25rem;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .try-it-btn:hover {
            background: var(--primary-dark);
        }
        
        .response-code {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }
        
        .response-code.success { background: #d1fae5; color: #065f46; }
        .response-code.error { background: #fee2e2; color: #991b1b; }
        
        @media (max-width: 1024px) {
            .container {
                grid-template-columns: 1fr;
            }
            
            .sidebar {
                position: static;
                height: auto;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <div class="logo">📚 {{ title }}</div>
            <span class="version">v{{ version }}</span>
        </div>
    </header>
    
    <div class="container">
        <aside class="sidebar">
            {% if enable_search %}
            <input type="text" class="search-box" placeholder="Search endpoints..." id="searchBox">
            {% endif %}
            
            <nav>
                <div class="nav-section">
                    <div class="nav-title">Overview</div>
                    <a href="#introduction" class="nav-item">Introduction</a>
                    <a href="#servers" class="nav-item">Servers</a>
                </div>
                
                <div class="nav-section">
                    <div class="nav-title">Endpoints</div>
                    {% for endpoint in endpoints %}
                    <a href="#{{ endpoint.operation_id }}" class="nav-item">
                        <span class="method {{ endpoint.method.value.lower() }}">{{ endpoint.method.value }}</span>
                        {{ endpoint.path }}
                    </a>
                    {% endfor %}
                </div>
            </nav>
        </aside>
        
        <main class="main-content">
            <div class="hero" id="introduction">
                <h1>{{ title }}</h1>
                <p>{{ description or "API Documentation" }}</p>
                
                {% if servers %}
                <div class="server-url">
                    Base URL: {{ servers[0].url }}
                </div>
                {% endif %}
            </div>
            
            {% for endpoint in endpoints %}
            <div class="endpoint" id="{{ endpoint.operation_id }}">
                <div class="endpoint-header">
                    <span class="method {{ endpoint.method.value.lower() }}">{{ endpoint.method.value }}</span>
                    <code class="path">{{ endpoint.path }}</code>
                    <span class="endpoint-summary">{{ endpoint.summary }}</span>
                </div>
                
                <div class="endpoint-body">
                    {% if endpoint.description %}
                    <div class="description">{{ endpoint.description }}</div>
                    {% endif %}
                    
                    {% if endpoint.parameters %}
                    <div class="section-title">Parameters</div>
                    <table class="params-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Type</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for param in endpoint.parameters %}
                            <tr>
                                <td>
                                    <span class="param-name">{{ param.name }}</span>
                                    {% if param.required %}<span class="param-required">*required</span>{% endif %}
                                </td>
                                <td><span class="param-type">{{ param.schema.type }}</span></td>
                                <td>{{ param.description or "-" }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% endif %}
                    
                    <div class="section-title">Responses</div>
                    {% for code, response in endpoint.responses.items() %}
                    <div class="response">
                        <span class="response-code {{ 'success' if code.startswith('2') else 'error' }}">{{ code }}</span>
                        {{ response.description }}
                    </div>
                    {% endfor %}
                    
                    {% if enable_try_it %}
                    <button class="try-it-btn">Try it</button>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </main>
    </div>
    
    {% if enable_search %}
    <script>
        document.getElementById('searchBox').addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            const endpoints = document.querySelectorAll('.endpoint');
            
            endpoints.forEach(function(endpoint) {
                const text = endpoint.textContent.toLowerCase();
                endpoint.style.display = text.includes(query) ? 'block' : 'none';
            });
        });
    </script>
    {% endif %}
</body>
</html>
'''
    
    def _copy_static_assets(self, output_dir: Path) -> None:
        """Copy static assets to output directory."""
        # Create assets directory
        assets_dir = output_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        # Copy custom CSS if provided
        if self.config.custom_css:
            shutil.copy2(self.config.custom_css, assets_dir / "custom.css")
        
        # Copy custom logo if provided
        if self.config.custom_logo:
            shutil.copy2(self.config.custom_logo, assets_dir / "logo.png")
    
    def _generate_markdown(self, spec: APISpec) -> Path:
        """Generate Markdown documentation."""
        output_file = self.config.output_path / "api.md"
        
        lines = [
            f"# {spec.title}",
            "",
            f"**Version:** {spec.version}",
            "",
        ]
        
        if spec.description:
            lines.extend([spec.description, ""])
        
        if spec.servers:
            lines.extend([
                "## Base URL",
                "",
                f"```\n{spec.servers[0].url}\n```",
                "",
            ])
        
        lines.extend(["## Endpoints", ""])
        
        for endpoint in spec.endpoints:
            lines.extend([
                f"### {endpoint.method.value} {endpoint.path}",
                "",
                f"**{endpoint.summary}**",
                "",
            ])
            
            if endpoint.description:
                lines.extend([endpoint.description, ""])
            
            if endpoint.parameters:
                lines.extend(["#### Parameters", "", "| Name | Type | Description |", "|------|------|-------------|"])
                for param in endpoint.parameters:
                    required = " (required)" if param.required else ""
                    lines.append(f"| `{param.name}`{required} | {param.schema.type} | {param.description or '-'} |")
                lines.append("")
            
            if endpoint.responses:
                lines.extend(["#### Responses", ""])
                for code, response in endpoint.responses.items():
                    lines.append(f"- **{code}**: {response.description}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        output_file.write_text("\n".join(lines), encoding="utf-8")
        return output_file
    
    def _generate_openapi_json(self, spec: APISpec) -> Path:
        """Generate OpenAPI JSON specification."""
        output_file = self.config.output_path / "openapi.json"
        openapi_spec = spec.to_openapi()
        
        output_file.write_text(
            json.dumps(openapi_spec, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return output_file
    
    def _generate_openapi_yaml(self, spec: APISpec) -> Path:
        """Generate OpenAPI YAML specification."""
        output_file = self.config.output_path / "openapi.yaml"
        openapi_spec = spec.to_openapi()
        
        output_file.write_text(
            yaml.dump(openapi_spec, default_flow_style=False, allow_unicode=True),
            encoding="utf-8"
        )
        return output_file
    
    def _generate_json(self, spec: APISpec) -> Path:
        """Generate JSON documentation."""
        output_file = self.config.output_path / "api.json"
        
        data = {
            "title": spec.title,
            "version": spec.version,
            "description": spec.description,
            "servers": [s.__dict__ for s in spec.servers],
            "endpoints": [
                {
                    "path": e.path,
                    "method": e.method.value,
                    "summary": e.summary,
                    "description": e.description,
                    "operationId": e.operation_id,
                    "tags": e.tags,
                }
                for e in spec.endpoints
            ],
        }
        
        output_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return output_file
    
    def _generate_yaml(self, spec: APISpec) -> Path:
        """Generate YAML documentation."""
        output_file = self.config.output_path / "api.yaml"
        
        data = {
            "title": spec.title,
            "version": spec.version,
            "description": spec.description,
            "servers": [s.__dict__ for s in spec.servers],
            "endpoints": [
                {
                    "path": e.path,
                    "method": e.method.value,
                    "summary": e.summary,
                    "description": e.description,
                    "operationId": e.operation_id,
                    "tags": e.tags,
                }
                for e in spec.endpoints
            ],
        }
        
        output_file.write_text(
            yaml.dump(data, default_flow_style=False, allow_unicode=True),
            encoding="utf-8"
        )
        return output_file
