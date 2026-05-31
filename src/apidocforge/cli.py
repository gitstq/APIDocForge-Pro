"""Command-line interface for APIDocForge."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from apidocforge.core.builder import DocumentBuilder
from apidocforge.models.config import Config, OutputFormat, ParserType

console = Console()


def print_banner() -> None:
    """Print the APIDocForge banner."""
    banner = Text()
    banner.append("🚀 ", style="bold cyan")
    banner.append("APIDocForge", style="bold blue")
    banner.append(" - AI-Powered API Documentation Generator\n", style="dim")
    banner.append("   Transform your code into beautiful API docs", style="dim italic")
    console.print(Panel(banner, border_style="blue"))


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version information")
@click.pass_context
def main(ctx: click.Context, version: bool) -> None:
    """🚀 APIDocForge - AI-Powered API Documentation Auto-Generation Engine"""
    if version:
        from apidocforge import __version__
        console.print(f"APIDocForge v{__version__}")
        return
    
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print("\n[dim]Run 'adf --help' for available commands[/dim]\n")


@main.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("-o", "--output", "output_path", type=click.Path(path_type=Path), default="./docs",
              help="Output directory for generated documentation")
@click.option("-f", "--format", "output_format", multiple=True,
              type=click.Choice(["html", "markdown", "openapi", "json", "yaml"], case_sensitive=False),
              default=["html"], help="Output format(s)")
@click.option("-t", "--title", default="API Documentation", help="API title")
@click.option("-v", "--version", "api_version", default="1.0.0", help="API version")
@click.option("-d", "--description", help="API description")
@click.option("--base-url", help="Base URL for API server")
@click.option("--parser", type=click.Choice(["auto", "python", "javascript", "typescript", "go", "java", "rust", "openapi"]),
              default="auto", help="Parser type")
@click.option("--theme", default="default", help="Documentation theme")
@click.option("--include", multiple=True, help="File patterns to include")
@click.option("--exclude", multiple=True, help="File patterns to exclude")
@click.option("--watch", is_flag=True, help="Watch for file changes and rebuild")
@click.option("--serve", is_flag=True, help="Start development server")
@click.option("--port", default=8080, help="Server port (with --serve)")
def generate(
    input_path: Path,
    output_path: Path,
    output_format: tuple,
    title: str,
    api_version: str,
    description: Optional[str],
    base_url: Optional[str],
    parser: str,
    theme: str,
    include: tuple,
    exclude: tuple,
    watch: bool,
    serve: bool,
    port: int,
) -> None:
    """Generate API documentation from source code."""
    print_banner()
    
    # Build configuration
    formats = [OutputFormat(f) for f in output_format]
    
    config = Config(
        input_path=input_path,
        output_path=output_path,
        output_formats=formats,
        parser_type=ParserType(parser),
        title=title,
        version=api_version,
        description=description,
        base_url=base_url,
        theme=theme,
        port=port,
    )
    
    # Override include/exclude patterns if provided
    if include:
        config.include_patterns = list(include)
    if exclude:
        config.exclude_patterns = list(exclude)
    
    builder = DocumentBuilder(config)
    
    # Show configuration
    table = Table(title="Configuration", border_style="blue")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Input Path", str(input_path))
    table.add_row("Output Path", str(output_path))
    table.add_row("Formats", ", ".join(f.value for f in formats))
    table.add_row("Parser", parser)
    table.add_row("Theme", theme)
    
    console.print(table)
    console.print()
    
    # Build documentation
    with console.status("[bold blue]Generating documentation...") as status:
        try:
            result = builder.build()
            
            # Show results
            console.print("[bold green]✅ Documentation generated successfully![/bold green]\n")
            
            results_table = Table(title="Generated Files", border_style="green")
            results_table.add_column("Format", style="cyan")
            results_table.add_column("Path", style="green")
            
            for fmt, path in result["output_files"].items():
                results_table.add_row(fmt, str(path))
            
            console.print(results_table)
            console.print(f"\n[dim]Total endpoints documented: {result['endpoint_count']}[/dim]")
            
        except Exception as e:
            console.print(f"[bold red]❌ Error: {e}[/bold red]")
            sys.exit(1)
    
    # Watch mode
    if watch:
        builder.watch()
    
    # Serve mode
    if serve:
        builder.serve()


@main.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("-p", "--port", default=8080, help="Server port")
@click.option("--host", default="127.0.0.1", help="Server host")
@click.option("-t", "--title", default="API Documentation", help="API title")
@click.option("-v", "--version", "api_version", default="1.0.0", help="API version")
def preview(
    input_path: Path,
    port: int,
    host: str,
    title: str,
    api_version: str,
) -> None:
    """Start a development server to preview documentation."""
    print_banner()
    
    config = Config(
        input_path=input_path,
        title=title,
        version=api_version,
        host=host,
        port=port,
    )
    
    builder = DocumentBuilder(config)
    builder.serve()


@main.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path), default=".")
@click.option("-o", "--output", "output_path", type=click.Path(path_type=Path), default="./docs",
              help="Output directory")
@click.option("-t", "--title", default="API Documentation", help="API title")
@click.option("-v", "--version", "api_version", default="1.0.0", help="API version")
def watch(
    input_path: Path,
    output_path: Path,
    title: str,
    api_version: str,
) -> None:
    """Watch source files for changes and rebuild documentation."""
    print_banner()
    
    config = Config(
        input_path=input_path,
        output_path=output_path,
        title=title,
        version=api_version,
    )
    
    builder = DocumentBuilder(config)
    
    # Initial build
    console.print("[bold blue]🔨 Initial build...[/bold blue]")
    builder.build()
    console.print("[bold green]✅ Initial build complete![/bold green]\n")
    
    # Start watching
    builder.watch()


@main.command()
@click.argument("spec_path", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", "output_path", type=click.Path(path_type=Path), default="./docs",
              help="Output directory")
@click.option("-f", "--format", "output_format", multiple=True,
              type=click.Choice(["html", "markdown"], case_sensitive=False),
              default=["html"], help="Output format(s)")
def convert(
    spec_path: Path,
    output_path: Path,
    output_format: tuple,
) -> None:
    """Convert OpenAPI/Swagger specification to documentation."""
    print_banner()
    
    from apidocforge.core.parser import CodeParser
    from apidocforge.models.config import Config
    
    config = Config(
        output_path=output_path,
        output_formats=[OutputFormat(f) for f in output_format],
    )
    
    parser = CodeParser(config)
    spec = parser.parse_openapi(spec_path)
    
    if not spec:
        console.print("[bold red]❌ Failed to parse OpenAPI specification[/bold red]")
        sys.exit(1)
    
    generator = APIDocGenerator(config)
    output_files = generator.generate(spec)
    
    console.print("[bold green]✅ Conversion complete![/bold green]\n")
    
    table = Table(title="Generated Files", border_style="green")
    table.add_column("Format", style="cyan")
    table.add_column("Path", style="green")
    
    for fmt, path in output_files.items():
        table.add_row(fmt, str(path))
    
    console.print(table)


@main.command()
def init() -> None:
    """Initialize a new APIDocForge configuration file."""
    print_banner()
    
    config_file = Path("apidocforge.toml")
    
    if config_file.exists():
        console.print("[yellow]⚠️  Configuration file already exists[/yellow]")
        return
    
    config_content = '''[tool.apidocforge]
title = "My API"
version = "1.0.0"
description = "API documentation generated by APIDocForge"
input_path = "."
output_path = "./docs"
output_formats = ["html", "openapi"]
parser_type = "auto"
theme = "default"
base_url = "https://api.example.com"

include_patterns = [
    "**/*.py",
    "**/*.js",
    "**/*.ts",
]

exclude_patterns = [
    "**/node_modules/**",
    "**/venv/**",
    "**/__pycache__/**",
    "**/tests/**",
]

[tool.apidocforge.features]
enable_code_samples = true
enable_try_it = true
enable_search = true
'''
    
    config_file.write_text(config_content, encoding="utf-8")
    console.print(f"[bold green]✅ Created {config_file}[/bold green]")
    console.print("\n[dim]Edit this file to customize your documentation settings[/dim]")


@main.command()
def list_themes() -> None:
    """List available documentation themes."""
    print_banner()
    
    table = Table(title="Available Themes", border_style="blue")
    table.add_column("Theme", style="cyan")
    table.add_column("Description", style="green")
    
    themes = [
        ("default", "Clean, modern documentation theme"),
        ("dark", "Dark mode optimized theme"),
        ("minimal", "Minimalist design with focus on content"),
    ]
    
    for theme, description in themes:
        table.add_row(theme, description)
    
    console.print(table)


if __name__ == "__main__":
    main()
