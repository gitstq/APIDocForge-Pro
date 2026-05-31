"""Document builder for orchestrating the documentation generation process."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from apidocforge.core.generator import APIDocGenerator
from apidocforge.core.parser import CodeParser
from apidocforge.models.api import APISpec
from apidocforge.models.config import Config, OutputFormat


class DocumentBuilder:
    """Orchestrates the API documentation generation process."""
    
    def __init__(self, config: Config) -> None:
        """Initialize builder with configuration."""
        self.config = config
        self.parser = CodeParser(config)
        self.generator = APIDocGenerator(config)
    
    def build(self) -> Dict[str, Any]:
        """Build API documentation from source code."""
        # Parse source code
        spec = self.parser.parse_directory(self.config.input_path)
        
        # Override with config values
        if self.config.title:
            spec.title = self.config.title
        if self.config.version:
            spec.version = self.config.version
        if self.config.description:
            spec.description = self.config.description
        if self.config.base_url:
            from apidocforge.models.api import Server
            spec.servers = [Server(url=self.config.base_url)]
        
        # Generate documentation
        output_files = self.generator.generate(spec)
        
        return {
            "spec": spec,
            "output_files": output_files,
            "endpoint_count": len(spec.endpoints),
        }
    
    def watch(self) -> None:
        """Watch source files for changes and rebuild."""
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class RebuildHandler(FileSystemEventHandler):
            def __init__(self, builder: DocumentBuilder) -> None:
                self.builder = builder
                self.last_build = 0
            
            def on_modified(self, event) -> None:
                if event.is_directory:
                    return
                
                # Check if file matches include patterns
                file_path = Path(event.src_path)
                for pattern in self.builder.config.include_patterns:
                    if file_path.match(pattern):
                        import time
                        current_time = time.time()
                        # Debounce: only rebuild if last build was more than 1 second ago
                        if current_time - self.last_build > 1:
                            print(f"\n📝 File changed: {file_path.name}")
                            print("🔄 Rebuilding documentation...")
                            self.builder.build()
                            print("✅ Documentation rebuilt successfully!")
                            self.last_build = current_time
                        break
        
        print(f"👀 Watching {self.config.input_path} for changes...")
        print("Press Ctrl+C to stop\n")
        
        event_handler = RebuildHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.config.input_path), recursive=True)
        observer.start()
        
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n👋 Stopping watcher...")
        
        observer.join()
    
    def serve(self) -> None:
        """Start a development server to preview documentation."""
        import uvicorn
        from fastapi import FastAPI
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        
        app = FastAPI(title=f"{self.config.title} - Preview")
        
        # Build documentation first
        result = self.build()
        output_dir = self.config.output_path / "html"
        
        # Mount static files
        if output_dir.exists():
            app.mount("/docs", StaticFiles(directory=str(output_dir), html=True), name="docs")
        
        @app.get("/")
        async def root() -> FileResponse:
            return FileResponse(str(output_dir / "index.html"))
        
        @app.get("/api/spec")
        async def get_spec() -> Dict[str, Any]:
            spec = result["spec"]
            return spec.to_openapi()
        
        print(f"\n🚀 Starting preview server at http://{self.config.host}:{self.config.port}")
        print(f"📚 Documentation: http://{self.config.host}:{self.config.port}/docs")
        print("Press Ctrl+C to stop\n")
        
        uvicorn.run(
            app,
            host=self.config.host,
            port=self.config.port,
            reload=self.config.reload,
        )
