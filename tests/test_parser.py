"""Tests for the code parser module."""

import pytest
from pathlib import Path

from apidocforge.core.parser import CodeParser
from apidocforge.models.config import Config


class TestCodeParser:
    """Test cases for CodeParser."""
    
    def test_detect_language_python(self) -> None:
        """Test language detection for Python files."""
        config = Config()
        parser = CodeParser(config)
        
        assert parser.detect_language(Path("test.py")) == "python"
        assert parser.detect_language(Path("test.PY")) == "python"
    
    def test_detect_language_javascript(self) -> None:
        """Test language detection for JavaScript files."""
        config = Config()
        parser = CodeParser(config)
        
        assert parser.detect_language(Path("test.js")) == "javascript"
        assert parser.detect_language(Path("test.mjs")) == "javascript"
    
    def test_detect_language_typescript(self) -> None:
        """Test language detection for TypeScript files."""
        config = Config()
        parser = CodeParser(config)
        
        assert parser.detect_language(Path("test.ts")) == "typescript"
        assert parser.detect_language(Path("test.tsx")) == "typescript"
    
    def test_detect_language_go(self) -> None:
        """Test language detection for Go files."""
        config = Config()
        parser = CodeParser(config)
        
        assert parser.detect_language(Path("test.go")) == "go"
    
    def test_detect_language_java(self) -> None:
        """Test language detection for Java files."""
        config = Config()
        parser = CodeParser(config)
        
        assert parser.detect_language(Path("test.java")) == "java"
    
    def test_detect_language_rust(self) -> None:
        """Test language detection for Rust files."""
        config = Config()
        parser = CodeParser(config)
        
        assert parser.detect_language(Path("test.rs")) == "rust"
    
    def test_detect_language_unknown(self) -> None:
        """Test language detection for unknown files."""
        config = Config()
        parser = CodeParser(config)
        
        assert parser.detect_language(Path("test.unknown")) is None
    
    def test_parse_python_fastapi(self) -> None:
        """Test parsing FastAPI routes from Python code."""
        config = Config()
        parser = CodeParser(config)
        
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    """Get all users."""
    return {"users": []}

@app.post("/users")
def create_user():
    """Create a new user."""
    return {"id": 1}
'''
        
        endpoints = parser._parse_python(code, Path("test.py"))
        
        assert len(endpoints) == 2
        assert endpoints[0].path == "/users"
        assert endpoints[0].method.value == "GET"
        assert endpoints[0].summary == "Get all users."
        assert endpoints[1].path == "/users"
        assert endpoints[1].method.value == "POST"
    
    def test_parse_python_flask(self) -> None:
        """Test parsing Flask routes from Python code."""
        config = Config()
        parser = CodeParser(config)
        
        code = '''
from flask import Flask

app = Flask(__name__)

@app.route("/users", methods=["GET"])
def get_users():
    """Get all users."""
    return {"users": []}
'''
        
        endpoints = parser._parse_python(code, Path("test.py"))
        
        assert len(endpoints) >= 1
        # Check if at least one endpoint was found
        get_endpoints = [e for e in endpoints if e.method.value == "GET"]
        assert len(get_endpoints) > 0
    
    def test_parse_javascript_express(self) -> None:
        """Test parsing Express routes from JavaScript code."""
        config = Config()
        parser = CodeParser(config)
        
        code = '''
const express = require('express');
const app = express();

/**
 * Get all users
 */
app.get('/users', (req, res) => {
    res.json({ users: [] });
});

app.post('/users', (req, res) => {
    res.json({ id: 1 });
});
'''
        
        endpoints = parser._parse_javascript(code, Path("test.js"))
        
        assert len(endpoints) == 2
        assert endpoints[0].path == "/users"
        assert endpoints[0].method.value == "GET"
        assert endpoints[1].path == "/users"
        assert endpoints[1].method.value == "POST"
    
    def test_extract_python_docstring(self) -> None:
        """Test extracting Python docstrings."""
        config = Config()
        parser = CodeParser(config)
        
        code = '''def test_func():
    """
    This is a test function.
    
    It does something useful.
    """
    pass
'''
        
        docstring = parser._extract_python_docstring(code, 0)
        assert "test function" in docstring
    
    def test_extract_jsdoc(self) -> None:
        """Test extracting JSDoc comments."""
        config = Config()
        parser = CodeParser(config)
        
        code = '''/**
 * Get all users
 * @returns {Array} List of users
 */
function getUsers() {}
'''
        
        jsdoc = parser._extract_jsdoc(code)
        assert "Get all users" in jsdoc


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
