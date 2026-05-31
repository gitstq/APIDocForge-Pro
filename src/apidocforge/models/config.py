"""Configuration models for APIDocForge."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set


class OutputFormat(Enum):
    """Supported output formats."""
    HTML = "html"
    MARKDOWN = "markdown"
    OPENAPI = "openapi"
    JSON = "json"
    YAML = "yaml"


class ParserType(Enum):
    """Supported parser types."""
    AUTO = "auto"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    RUST = "rust"
    OPENAPI = "openapi"


@dataclass
class Config:
    """APIDocForge configuration."""
    
    # Input settings
    input_path: Path = field(default_factory=lambda: Path("."))
    parser_type: ParserType = ParserType.AUTO
    include_patterns: List[str] = field(default_factory=lambda: ["**/*.py", "**/*.js", "**/*.ts", "**/*.go", "**/*.java", "**/*.rs"])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "**/node_modules/**",
        "**/venv/**",
        "**/.venv/**",
        "**/__pycache__/**",
        "**/dist/**",
        "**/build/**",
        "**/tests/**",
        "**/test_*.py",
        "**/*_test.py",
    ])
    
    # Output settings
    output_path: Path = field(default_factory=lambda: Path("./docs"))
    output_format: OutputFormat = OutputFormat.HTML
    output_formats: List[OutputFormat] = field(default_factory=lambda: [OutputFormat.HTML])
    
    # API Info
    title: str = "API Documentation"
    version: str = "1.0.0"
    description: Optional[str] = None
    base_url: Optional[str] = None
    
    # Server settings
    host: str = "127.0.0.1"
    port: int = 8080
    reload: bool = False
    
    # Feature flags
    enable_ai_enhancement: bool = False
    enable_code_samples: bool = True
    enable_try_it: bool = True
    enable_search: bool = True
    
    # Theme settings
    theme: str = "default"
    custom_css: Optional[Path] = None
    custom_logo: Optional[Path] = None
    
    # Language settings
    language: str = "en"
    
    # AI settings (for future expansion)
    ai_provider: Optional[str] = None
    ai_api_key: Optional[str] = None
    ai_model: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Ensure paths are Path objects
        if isinstance(self.input_path, str):
            self.input_path = Path(self.input_path)
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)
        if self.custom_css and isinstance(self.custom_css, str):
            self.custom_css = Path(self.custom_css)
        if self.custom_logo and isinstance(self.custom_logo, str):
            self.custom_logo = Path(self.custom_logo)
    
    @classmethod
    def from_dict(cls, data: Dict) -> Config:
        """Create configuration from dictionary."""
        # Handle enum conversions
        if "parser_type" in data and isinstance(data["parser_type"], str):
            data["parser_type"] = ParserType(data["parser_type"])
        if "output_format" in data and isinstance(data["output_format"], str):
            data["output_format"] = OutputFormat(data["output_format"])
        if "output_formats" in data:
            data["output_formats"] = [
                OutputFormat(f) if isinstance(f, str) else f
                for f in data["output_formats"]
            ]
        
        # Handle path conversions
        for key in ["input_path", "output_path", "custom_css", "custom_logo"]:
            if key in data and data[key] is not None:
                data[key] = Path(data[key])
        
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            "input_path": str(self.input_path),
            "parser_type": self.parser_type.value,
            "include_patterns": self.include_patterns,
            "exclude_patterns": self.exclude_patterns,
            "output_path": str(self.output_path),
            "output_format": self.output_format.value,
            "output_formats": [f.value for f in self.output_formats],
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "base_url": self.base_url,
            "host": self.host,
            "port": self.port,
            "reload": self.reload,
            "enable_ai_enhancement": self.enable_ai_enhancement,
            "enable_code_samples": self.enable_code_samples,
            "enable_try_it": self.enable_try_it,
            "enable_search": self.enable_search,
            "theme": self.theme,
            "custom_css": str(self.custom_css) if self.custom_css else None,
            "custom_logo": str(self.custom_logo) if self.custom_logo else None,
            "language": self.language,
        }
