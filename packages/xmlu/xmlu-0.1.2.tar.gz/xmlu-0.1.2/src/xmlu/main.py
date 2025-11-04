from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .convert_to_json import xml_to_json
from .convert_to_pydantic import create_models_file, generate_pydantic_models

console = Console()

app = typer.Typer(
    name="xmlu",
    help="XML Utility - Generate Pydantic models from XML files",
    add_completion=False,
    invoke_without_command=True,
)


def get_version() -> str:
    """Retrieve the current version of the xmlu package."""
    import importlib.metadata

    try:
        return importlib.metadata.version("xmlu")
    except importlib.metadata.PackageNotFoundError:
        return "development"


def _print_banner() -> None:
    """Print a cool ASCII art banner for XMLU."""
    banner = """
██╗  ██╗███╗   ███╗██╗     ██╗   ██╗
╚██╗██╔╝████╗ ████║██║     ██║   ██║
 ╚███╔╝ ██╔████╔██║██║     ██║   ██║
 ██╔██╗ ██║╚██╔╝██║██║     ██║   ██║
██╔╝ ██╗██║ ╚═╝ ██║███████╗╚██████╔╝
╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝ ╚═════╝ 
"""

    description = Text(
        "XML Utility - Generate Pydantic models from XML files", style="cyan"
    )
    subtitle = Text("Transform your XML into type-safe Python models", style="dim")
    version_info = Text(f"v{get_version()}", style="bold cyan")
    description.append(" • ")
    description.append(version_info)

    panel_content = Text()
    panel_content.append(banner, style="bold bright_cyan")
    panel_content.append("\n")
    panel_content.append(description)
    panel_content.append("\n")
    panel_content.append(subtitle)

    panel = Panel(
        panel_content,
        border_style="bright_cyan",
        padding=(1, 2),
        title="[bold bright_cyan]Welcome[/bold bright_cyan]",
        title_align="left",
    )

    console.print(panel)
    console.print()


@app.callback()
def main(ctx: typer.Context) -> None:
    """XML Utility CLI - Generate Pydantic models from XML files."""
    if ctx.invoked_subcommand is None:
        _print_banner()
        console.print("[bold]Available commands:[/bold]")
        console.print(
            "  [cyan]generate[/cyan]  Generate Pydantic models from an XML file"
        )
        console.print("  [cyan]xml-to-json[/cyan]  Convert an XML file to JSON format")
        console.print("  [cyan]version[/cyan]    Show version information")
        console.print()
        console.print(
            "Run [cyan]xmlu --help[/cyan] or [cyan]xmlu [command] --help[/cyan] for more information."
        )
        console.print()


def _validate_xml_file(file_path: Path) -> None:
    """Validate that the XML file exists and is readable."""
    if not file_path.exists():
        console.print(f"[red]Error:[/red] File not found: {file_path}")
        raise typer.Exit(code=1)

    if not file_path.is_file():
        console.print(f"[red]Error:[/red] Path is not a file: {file_path}")
        raise typer.Exit(code=1)

    if file_path.suffix.lower() not in (".xml", ".sch"):
        console.print(
            f"[yellow]Warning:[/yellow] File doesn't have .xml or .sch extension: {file_path}"
        )


@app.command(
    name="generate",
    help="Generate Pydantic models from an XML file",
)
def generate(
    file_path: Path = typer.Argument(
        ...,
        help="Path to the XML file to process",
        exists=True,
    ),
    parent_element: str = typer.Option(
        "Event",
        "--parent",
        "-p",
        help="XML tag name to use as the parent model (default: Event)",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: auto-generated based on XML root tag)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed progress information",
    ),
) -> None:
    """
    Generate Pydantic models from an XML file.

    This command analyzes the XML structure and creates typed Pydantic models with:
    - Automatic type inference (str, int, bool)
    - Optional/Required field detection
    - Nested model support for elements with Name/Value attributes
    - Proper model relationships and field aliases

    Example:
        xmlu generate schedule.xml --parent Event
        xmlu generate data.xml -p Item -o models.py
    """
    _validate_xml_file(file_path)

    console.print(f"[cyan]📄 Processing XML file:[/cyan] {file_path}")

    if verbose:
        console.print(f"   [blue]Parent element:[/blue] {parent_element}")

    try:
        if verbose:
            console.print("   [blue]Analyzing XML structure...[/blue]")

        models = generate_pydantic_models(str(file_path), parent_element)

        if verbose:
            console.print(f"   [blue]Generated {len(models)} model(s)[/blue]")
            console.print(f"   [blue]- Parent model:[/blue] {models[0].__name__}")
            if len(models) > 1:
                nested_models = [m.__name__ for m in models[1:]]
                console.print(
                    f"   [blue]- Nested models:[/blue] {', '.join(nested_models)}"
                )

        if verbose:
            console.print("   [blue]Writing models to file...[/blue]")

        output_file = create_models_file(str(file_path), list(models))

        if output:
            # If output path specified, move/rename the file
            generated_path = Path(output_file)
            if generated_path.exists():
                # Ensure output directory exists
                output.parent.mkdir(parents=True, exist_ok=True)
                generated_path.rename(output)
                output_file = str(output)

        console.print(
            f"[green]✅ Successfully generated models in:[/green] {output_file}"
        )

        if verbose:
            model_names = [m.__name__ for m in models]
            console.print(f"   [blue]Models:[/blue] {', '.join(model_names)}")

    except FileNotFoundError:
        console.print(f"[red]Error:[/red] File not found: {file_path}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to process XML file: {e}")
        if verbose:
            import traceback

            console.print(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(code=1)


@app.command(
    name="xml-to-json",
    help="Convert an XML file to JSON format",
)
def xml_to_json_command(
    file_path: Path = typer.Argument(),
    output: Path = typer.Option(None, "--output", "-o", help="Output JSON file path"),
) -> None:
    xml_to_json(file_path, output_file=output)


@app.command(
    name="version",
    help="Show version information",
)
def version() -> None:
    """Display the version of xmlu."""
    import importlib.metadata

    try:
        version_str = importlib.metadata.version("xmlu")
        console.print(f"[cyan]xmlu version {version_str}[/cyan]")
    except importlib.metadata.PackageNotFoundError:
        console.print("[cyan]xmlu (development version)[/cyan]")
