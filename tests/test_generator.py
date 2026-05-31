"""Tests for the documentation generator module."""

import json
from pathlib import Path

import pytest
import yaml

from apidocforge.core.generator import APIDocGenerator
from apidocforge.models.api import APISpec, Endpoint, HTTPMethod, Response, Schema, Server
from apidocforge.models.config import Config, OutputFormat


class TestAPIDocGenerator:
    """Test cases for APIDocGenerator."""
    
    @pytest.fixture
    def sample_spec(self) -> APISpec:
        """Create a sample API spec for testing."""
        return APISpec(
            title="Test API",
            version="1.0.0",
            description="A test API for unit testing",
            servers=[Server(url="https://api.example.com", description="Production")],
            endpoints=[
                Endpoint(
                    path="/users",
                    method=HTTPMethod.GET,
                    summary="Get all users",
                    description="Returns a list of all users",
                    operation_id="get_users",
                    tags=["Users"],
                    responses={
                        "200": Response(
                            status_code="200",
                            description="Successful response",
                            schema=Schema(type="array")
                        )
                    }
                ),
                Endpoint(
                    path="/users",
                    method=HTTPMethod.POST,
                    summary="Create user",
                    description="Creates a new user",
                    operation_id="create_user",
                    tags=["Users"],
                    responses={
                        "201": Response(
                            status_code="201",
                            description="User created",
                            schema=Schema(type="object")
                        )
                    }
                ),
            ],
        )
    
    @pytest.fixture
    def temp_output_dir(self, tmp_path: Path) -> Path:
        """Create a temporary output directory."""
        return tmp_path / "docs"
    
    def test_generate_html(self, sample_spec: APISpec, temp_output_dir: Path) -> None:
        """Test HTML documentation generation."""
        config = Config(
            output_path=temp_output_dir,
            output_formats=[OutputFormat.HTML],
        )
        generator = APIDocGenerator(config)
        
        output_files = generator.generate(sample_spec)
        
        assert "html" in output_files
        assert output_files["html"].exists()
        
        content = output_files["html"].read_text()
        assert "Test API" in content
        assert "Get all users" in content
        assert "Create user" in content
    
    def test_generate_markdown(self, sample_spec: APISpec, temp_output_dir: Path) -> None:
        """Test Markdown documentation generation."""
        config = Config(
            output_path=temp_output_dir,
            output_formats=[OutputFormat.MARKDOWN],
        )
        generator = APIDocGenerator(config)
        
        output_files = generator.generate(sample_spec)
        
        assert "markdown" in output_files
        assert output_files["markdown"].exists()
        
        content = output_files["markdown"].read_text()
        assert "Test API" in content
        assert "GET /users" in content
        assert "POST /users" in content
    
    def test_generate_openapi_json(self, sample_spec: APISpec, temp_output_dir: Path) -> None:
        """Test OpenAPI JSON generation."""
        config = Config(
            output_path=temp_output_dir,
            output_formats=[OutputFormat.OPENAPI],
        )
        generator = APIDocGenerator(config)
        
        output_files = generator.generate(sample_spec)
        
        assert "openapi_json" in output_files
        assert output_files["openapi_json"].exists()
        
        content = json.loads(output_files["openapi_json"].read_text())
        assert content["openapi"] == "3.0.3"
        assert content["info"]["title"] == "Test API"
        assert "/users" in content["paths"]
    
    def test_generate_openapi_yaml(self, sample_spec: APISpec, temp_output_dir: Path) -> None:
        """Test OpenAPI YAML generation."""
        config = Config(
            output_path=temp_output_dir,
            output_formats=[OutputFormat.OPENAPI],
        )
        generator = APIDocGenerator(config)
        
        output_files = generator.generate(sample_spec)
        
        assert "openapi_yaml" in output_files
        assert output_files["openapi_yaml"].exists()
        
        content = yaml.safe_load(output_files["openapi_yaml"].read_text())
        assert content["openapi"] == "3.0.3"
        assert content["info"]["title"] == "Test API"
    
    def test_generate_json(self, sample_spec: APISpec, temp_output_dir: Path) -> None:
        """Test JSON documentation generation."""
        config = Config(
            output_path=temp_output_dir,
            output_formats=[OutputFormat.JSON],
        )
        generator = APIDocGenerator(config)
        
        output_files = generator.generate(sample_spec)
        
        assert "json" in output_files
        assert output_files["json"].exists()
        
        content = json.loads(output_files["json"].read_text())
        assert content["title"] == "Test API"
        assert len(content["endpoints"]) == 2
    
    def test_generate_yaml(self, sample_spec: APISpec, temp_output_dir: Path) -> None:
        """Test YAML documentation generation."""
        config = Config(
            output_path=temp_output_dir,
            output_formats=[OutputFormat.YAML],
        )
        generator = APIDocGenerator(config)
        
        output_files = generator.generate(sample_spec)
        
        assert "yaml" in output_files
        assert output_files["yaml"].exists()
        
        content = yaml.safe_load(output_files["yaml"].read_text())
        assert content["title"] == "Test API"
        assert len(content["endpoints"]) == 2
    
    def test_generate_multiple_formats(self, sample_spec: APISpec, temp_output_dir: Path) -> None:
        """Test generating documentation in multiple formats."""
        config = Config(
            output_path=temp_output_dir,
            output_formats=[OutputFormat.HTML, OutputFormat.MARKDOWN, OutputFormat.OPENAPI],
        )
        generator = APIDocGenerator(config)
        
        output_files = generator.generate(sample_spec)
        
        assert "html" in output_files
        assert "markdown" in output_files
        assert "openapi_json" in output_files
        assert "openapi_yaml" in output_files


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
