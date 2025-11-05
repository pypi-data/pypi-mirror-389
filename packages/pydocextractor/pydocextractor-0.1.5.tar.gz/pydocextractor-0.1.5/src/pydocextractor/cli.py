"""
CLI interface for pyDocExtractor using hexagonal architecture.

Provides command-line tools for converting documents to Markdown.
"""

from __future__ import annotations

import time
import traceback
import warnings
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import __version__
from .domain.models import Document, PrecisionLevel
from .domain.rules import calculate_document_hash, hint_has_tables
from .factory import create_converter_service, get_available_extractors

# Suppress PyTorch MPS warning on Apple Silicon
# This warning is harmless - pin_memory doesn't work on MPS devices yet
# but doesn't affect functionality. It's triggered by docling's PyTorch usage.
warnings.filterwarnings(
    "ignore",
    message=".*pin_memory.*not supported on MPS.*",
    category=UserWarning,
)

app = typer.Typer(
    name="pydocextractor",
    help="Convert documents (PDF, DOCX, XLSX) to Markdown with multiple precision levels",
    add_completion=False,
)
console = Console()


def _load_document(file_path: Path, precision: PrecisionLevel) -> Document:
    """Load document from file."""
    # Read file bytes
    data = file_path.read_bytes()

    # Detect MIME type
    suffix = file_path.suffix.lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".csv": "text/csv",
    }
    mime = mime_map.get(suffix, "application/octet-stream")

    return Document(
        bytes=data,
        mime=mime,
        size_bytes=len(data),
        precision=precision,
        filename=file_path.name,
    )


@app.command()
def convert(
    input_file: Path = typer.Argument(..., help="Path to the document to convert"),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="Output markdown file path"
    ),
    precision_level: int | None = typer.Option(
        None,
        "--level",
        "-l",
        min=1,
        max=4,
        help="Precision level (1=fastest, 4=highest quality). Auto-select if not specified.",
    ),
    show_score: bool = typer.Option(False, "--show-score", "-s", help="Show quality score"),
    show_hash: bool = typer.Option(False, "--show-hash", "-h", help="Show file hash (SHA-256)"),
    template: str = typer.Option(
        "default", "--template", "-t", help="Template name (default, simple)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Convert a document to Markdown."""
    # Validate input file
    if not input_file.exists():
        console.print(f"[red]Error: File not found: {input_file}[/red]")
        raise typer.Exit(1)

    # Set output file if not specified
    if output_file is None:
        output_file = input_file.with_suffix(".md")

    # Map precision level
    if precision_level is None:
        precision = PrecisionLevel.BALANCED
    else:
        precision_map = {
            1: PrecisionLevel.FASTEST,
            2: PrecisionLevel.BALANCED,
            3: PrecisionLevel.TABLE_OPTIMIZED,
            4: PrecisionLevel.HIGHEST_QUALITY,
        }
        precision = precision_map[precision_level]

    # Auto-select template for tabular data if user didn't specify
    if template == "default":
        tabular_extensions = {".csv", ".xlsx", ".xls"}
        if input_file.suffix.lower() in tabular_extensions:
            template = "tabular"

    console.print(f"\n[bold]Converting:[/bold] {input_file}")
    console.print(f"[bold]Precision Level:[/bold] {precision.name} (Level {precision.value})")
    console.print(f"[bold]Template:[/bold] {template}")

    # Create service
    try:
        service = create_converter_service()
    except Exception as e:
        console.print(f"[red]Failed to initialize converter: {e}[/red]")
        raise typer.Exit(1) from e

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Converting document...", total=None)

        try:
            # Load document
            doc = _load_document(input_file, precision)

            # Convert
            start_time = time.time()
            result = service.convert_to_markdown(doc, template_name=template)
            elapsed = time.time() - start_time

            progress.update(task, completed=True)
        except Exception as e:
            progress.stop()
            console.print(f"[red]Conversion failed: {e}[/red]")
            if verbose:
                console.print(traceback.format_exc())
            raise typer.Exit(1) from e

    # Write output
    try:
        output_file.write_text(result.text, encoding="utf-8")
        console.print("[green]✓ Converted successfully![/green]")
        console.print(f"[bold]Output:[/bold] {output_file}")
    except Exception as e:
        console.print(f"[red]Failed to write output file: {e}[/red]")
        raise typer.Exit(1) from e

    # Show stats
    console.print("\n[bold]Stats:[/bold]")
    extractor_name = result.metadata.get("extractor", "Unknown")
    console.print(f"  Extractor: {extractor_name}")
    console.print(f"  Processing time: {elapsed:.2f}s")
    console.print(f"  Output length: {len(result.text):,} characters")

    if show_score and result.quality_score is not None:
        # Constants for quality score colors
        GOOD_QUALITY_THRESHOLD = 0.7
        score_color = "green" if result.quality_score >= GOOD_QUALITY_THRESHOLD else "yellow"
        console.print(f"  Quality score: [{score_color}]{result.quality_score:.2f}[/{score_color}]")

    if show_hash:
        file_hash = calculate_document_hash(doc)
        console.print(f"  SHA-256: {file_hash}")


@app.command()
def batch(
    input_dir: Path = typer.Argument(..., help="Directory containing documents"),
    output_dir: Path = typer.Argument(..., help="Output directory for markdown files"),
    precision_level: int | None = typer.Option(
        None,
        "--level",
        "-l",
        min=1,
        max=4,
        help="Precision level for all documents",
    ),
    pattern: str = typer.Option(
        "all",
        "--pattern",
        "-p",
        help="File pattern to match (e.g., '*.pdf', '*.csv', 'all' for all supported formats)",
    ),
    template: str = typer.Option("default", "--template", "-t", help="Template name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Convert multiple documents in a directory."""
    # Validate input directory
    if not input_dir.exists() or not input_dir.is_dir():
        console.print(f"[red]Error: Directory not found: {input_dir}[/red]")
        raise typer.Exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Expand pattern to supported formats
    if pattern == "all":
        # Default: scan all supported formats
        patterns = ["*.pdf", "*.docx", "*.xlsx", "*.xls", "*.csv"]
    else:
        patterns = [pattern]

        # Find matching files
    all_files: list[str] = []
    for pat in patterns:
        all_files.extend(str(f) for f in input_dir.glob(pat))

    # Filter out Office temporary files (starting with ~$) and remove duplicates
    seen = set()
    files = []
    for f in all_files:
        file_path = Path(f)
        if not file_path.name.startswith("~$") and f not in seen:
            files.append(f)
            seen.add(f)

    if not files:
        console.print(f"[yellow]No files found matching pattern: {pattern}[/yellow]")
        raise typer.Exit(0)

    console.print(f"\n[bold]Found {len(files)} file(s) to convert[/bold]\n")

    # Map precision level
    if precision_level is None:
        precision = PrecisionLevel.BALANCED
    else:
        precision_map = {
            1: PrecisionLevel.FASTEST,
            2: PrecisionLevel.BALANCED,
            3: PrecisionLevel.TABLE_OPTIMIZED,
            4: PrecisionLevel.HIGHEST_QUALITY,
        }
        precision = precision_map[precision_level]

    # Create service
    try:
        service = create_converter_service()
    except Exception as e:
        console.print(f"[red]Failed to initialize converter: {e}[/red]")
        raise typer.Exit(1) from e

    # Convert each file
    success_count = 0
    fail_count = 0
    batch_start_time = time.time()

    with Progress(console=console) as progress:
        task = progress.add_task("[cyan]Converting...", total=len(files))

        for file_path_str in files:
            try:
                # Load document
                file_path_obj = Path(file_path_str)
                doc = _load_document(file_path_obj, precision)

                # Auto-select template for tabular data if user didn't specify
                selected_template = template
                if template == "default":
                    tabular_extensions = {".csv", ".xlsx", ".xls"}
                    if file_path_obj.suffix.lower() in tabular_extensions:
                        selected_template = "tabular"

                # Convert
                result = service.convert_to_markdown(doc, template_name=selected_template)

                # Write output
                output_file = output_dir / file_path_obj.with_suffix(".md").name
                output_file.write_text(result.text, encoding="utf-8")

                success_count += 1
                console.print(f"[green]✓[/green] {file_path_obj.name}")
            except Exception as e:
                fail_count += 1
                error_msg = str(e) if not verbose else f"{e}\n{traceback.format_exc()}"
                console.print(f"[red]✗[/red] {file_path_obj.name}: {error_msg}")

            progress.update(task, advance=1)

    batch_elapsed_time = time.time() - batch_start_time

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Successful: [green]{success_count}[/green]")
    console.print(f"  Failed: [red]{fail_count}[/red]")
    console.print(f"  Total: {len(files)}")
    console.print(f"  Total time: {batch_elapsed_time:.2f}s")
    if success_count > 0:
        avg_time = batch_elapsed_time / success_count
        console.print(f"  Average time per file: {avg_time:.2f}s")


@app.command()
def status() -> None:
    """Show status of available converters."""
    console.print("\n[bold]pyDocExtractor - Converter Status[/bold]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Level", style="cyan", justify="center")
    table.add_column("Name", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Features")

    converters_info = [
        (PrecisionLevel.FASTEST, "ChunkedParallel", "Fastest, parallel processing"),
        (PrecisionLevel.BALANCED, "PyMuPDF4LLM", "Balanced, LLM-optimized (default)"),
        (PrecisionLevel.TABLE_OPTIMIZED, "PDFPlumber", "Table extraction, structured data"),
        (PrecisionLevel.HIGHEST_QUALITY, "Docling", "Highest quality, multi-format"),
    ]

    available_extractors = get_available_extractors()
    available_levels = {ext.precision_level for ext in available_extractors}

    for level, name, features in converters_info:
        if level in available_levels:
            status_str = "[green]✓ Available[/green]"
        else:
            status_str = "[red]✗ Not Available[/red]"

        table.add_row(str(level.value), name, status_str, features)

    console.print(table)

    console.print(f"\n[bold]Total available:[/bold] {len(available_extractors)}/4\n")


@app.command()
def info(file_path: Path = typer.Argument(..., help="Path to document to analyze")) -> None:
    """Show information about a document."""
    if not file_path.exists():
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Document Information:[/bold] {file_path.name}\n")

    # Load document
    doc = _load_document(file_path, PrecisionLevel.BALANCED)

    # Basic info
    console.print(f"[bold]Path:[/bold] {file_path}")
    console.print(f"[bold]Format:[/bold] {file_path.suffix}")
    console.print(f"[bold]Size:[/bold] {doc.size_bytes / (1024 * 1024):.2f} MB")
    console.print(f"[bold]MIME:[/bold] {doc.mime}")
    console.print(f"[bold]SHA-256:[/bold] {calculate_document_hash(doc)}")

    # PDF-specific info
    if doc.mime == "application/pdf":
        try:
            import fitz

            pdf_doc = fitz.open(stream=doc.bytes, filetype="pdf")
            console.print(f"[bold]Pages:[/bold] {pdf_doc.page_count}")
            pdf_doc.close()

            has_tables = hint_has_tables(doc)
            tables_str = "[green]Yes[/green]" if has_tables else "[yellow]No[/yellow]"
            console.print(f"[bold]Tables detected:[/bold] {tables_str}")
        except ImportError:
            console.print("[yellow]Install PyMuPDF for detailed PDF information[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Could not analyze PDF: {e}[/yellow]")

    # Recommended converter
    try:
        # Get available extractors
        extractors = get_available_extractors()
        if extractors:
            # Get recommended extractor based on document
            has_tables = hint_has_tables(doc)
            if has_tables:
                recommended = "PDFPlumber (Level 3) - Document has tables"
            elif doc.size_bytes > 20 * 1024 * 1024:
                recommended = "ChunkedParallel (Level 1) - Large file"
            elif doc.size_bytes < 2 * 1024 * 1024:
                recommended = "Docling (Level 4) - Small file, highest quality"
            else:
                recommended = "PyMuPDF4LLM (Level 2) - Default, balanced"

            console.print(f"\n[bold]Recommended converter:[/bold] {recommended}")
    except Exception as e:
        console.print(f"\n[yellow]Could not determine recommended converter: {e}[/yellow]")

    console.print()


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"\n[bold]pyDocExtractor[/bold] version {__version__}\n")


def main() -> None:
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
