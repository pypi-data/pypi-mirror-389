"""Main CLI interface for fuzzygrep with configuration management."""

import atexit
import collections
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from fuzzygrep.core.searcher import FuzzySearcher
from fuzzygrep.ui.display import ResultsDisplay
from fuzzygrep.ui.interactive import InteractiveSession
from fuzzygrep.utils.errors import FuzzyGrepError
from fuzzygrep.utils.logging import cleanup_logger, setup_logger

# Check for required dependencies
REQUIRED_PACKAGES = {
    'rapidfuzz': 'rapidfuzz',
    'typer': 'typer',
    'rich': 'rich',
    'prompt_toolkit': 'prompt_toolkit',
    'cachetools': 'cachetools'
}

missing_packages = []
for module_name, package_name in REQUIRED_PACKAGES.items():
    try:
        __import__(module_name)
    except ImportError:
        missing_packages.append(package_name)

if missing_packages:
    print(f"❌ Error: Missing required dependencies: {', '.join(missing_packages)}")
    print(f"\n💡 To install, run:")
    print(f"   pip install -r requirements.txt")
    print(f"   OR")
    print(f"   pip install {' '.join(missing_packages)}")
    sys.exit(1)

# Create CLI app
app = typer.Typer(
    name="fuzzygrep",
    help="""Interactive fuzzy search for JSON and CSV files.
    
    Quick start: fuzzygrep main FILE_PATH
    
    Run 'fuzzygrep main --help' for search options.""",
    add_completion=True,
    no_args_is_help=True
)

console = Console()


# Cleanup on exit
@atexit.register
def cleanup():
    """Cleanup resources on exit."""
    cleanup_logger()


@app.command()
def main(
    file_path: Optional[Path] = typer.Argument(
        None,
        help="Path to the JSON or CSV file to search",
        exists=False,
        dir_okay=False,
        resolve_path=True
    ),
    chart: bool = typer.Option(
        False,
        "--chart",
        "-c",
        help="Display a tree visualization of the file structure and exit"
    ),
    chart_limit: int = typer.Option(
        100,
        "--chart-limit",
        help="Maximum number of list items to show in chart (0 for unlimited)"
    ),
    histogram: bool = typer.Option(
        False,
        "--histogram",
        "-H",
        help="Display frequency histograms for keys and values and exit"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging output"
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Disable caching"
    ),
    no_index: bool = typer.Option(
        False,
        "--no-index",
        help="Disable search indexing"
    ),
    no_parallel: bool = typer.Option(
        False,
        "--no-parallel",
        help="Disable parallel processing"
    ),
    workers: Optional[int] = typer.Option(
        None,
        "--workers",
        "-w",
        help="Number of worker processes for parallel operations"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        "-i/-I",
        help="Start interactive session (default: True)"
    )
):
    """
    Fuzzygrep - Interactive fuzzy search for JSON and CSV files.
    
    \b
    Examples:
        fuzzygrep data.json                    # Interactive search
        fuzzygrep data.csv --chart             # Show tree visualization
        fuzzygrep data.json --histogram        # Show histograms
        fuzzygrep data.json --verbose          # Enable verbose logging
        fuzzygrep large.json --no-cache        # Disable caching
    """
    # Validate file_path is provided
    if file_path is None:
        console.print("[red]❌ Error: Missing required argument[/red]")
        console.print("\n[yellow]Usage:[/yellow] fuzzygrep [cyan]FILE_PATH[/cyan] [OPTIONS]")
        console.print("\n[dim]FILE_PATH must be a path to a JSON or CSV file[/dim]")
        console.print("\n[bold]Examples:[/bold]")
        console.print("  fuzzygrep data.json")
        console.print("  fuzzygrep data.csv --chart")
        console.print("  fuzzygrep data.json --histogram")
        console.print("\n[dim]For more help, run:[/dim] fuzzygrep --help")
        raise typer.Exit(code=1)
    
    # Validate file exists
    if not file_path.exists():
        console.print(f"[red]❌ Error: File not found:[/red] {file_path}")
        console.print(f"\n[yellow]Please check that the file path is correct:[/yellow]")
        console.print(f"  {file_path.absolute()}")
        console.print("\n[dim]💡 Tip: Use tab completion or check the file path[/dim]")
        raise typer.Exit(code=1)
    
    # Validate file is not a directory
    if file_path.is_dir():
        console.print(f"[red]❌ Error: Expected a file, but got a directory:[/red] {file_path}")
        console.print(f"\n[yellow]Please provide a JSON or CSV file, not a directory[/yellow]")
        console.print("\n[dim]💡 Tip: Navigate into the directory and specify a file[/dim]")
        raise typer.Exit(code=1)
    
    # Validate file extension
    if file_path.suffix.lower() not in ['.json', '.csv']:
        console.print(f"[red]⚠️  Warning: File extension '{file_path.suffix}' is not .json or .csv[/red]")
        console.print("[yellow]Fuzzygrep works best with JSON and CSV files[/yellow]")
        console.print("\n[dim]Continuing anyway...[/dim]\n")
    
    # Setup logging
    logger = setup_logger(verbose=verbose)
    
    try:
        # Create searcher
        searcher = FuzzySearcher(
            file_path,
            use_cache=not no_cache,
            use_index=not no_index,
            parallel=not no_parallel,
            max_workers=workers
        )
        
        display = ResultsDisplay(console)
        
        # Handle chart mode
        if chart:
            if searcher.data:
                console.print(f"\n[bold cyan]File Structure: {file_path.name}[/bold cyan]\n")
                display.display_tree(searcher.data, name=str(file_path.name), max_items=chart_limit)
            else:
                console.print("[red]Could not generate chart - data failed to load[/red]")
            raise typer.Exit()
        
        # Handle histogram mode
        if histogram:
            if searcher.data:
                _show_histogram(searcher, display)
            else:
                console.print("[red]Could not generate histogram - data failed to load[/red]")
            raise typer.Exit()
        
        # Start interactive session
        if interactive:
            session = InteractiveSession(searcher)
            session.run()
        else:
            console.print("[yellow]Non-interactive mode: use --chart or --histogram[/yellow]")
    
    except FuzzyGrepError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=130)
    
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)


def _show_histogram(searcher: FuzzySearcher, display: ResultsDisplay):
    """Show histogram visualizations."""
    from fuzzygrep.core.loaders import KeyValueExtractor
    
    console.print(f"\n[bold cyan]Frequency Analysis[/bold cyan]\n")
    
    # Extract all keys and values
    all_keys = KeyValueExtractor.extract_keys(searcher.data)
    all_values = KeyValueExtractor.extract_values(searcher.data)
    
    # Count frequencies
    key_counts = collections.Counter(all_keys)
    value_counts = collections.Counter(all_values)
    
    # Display key histogram
    if key_counts:
        display.display_histogram(
            dict(key_counts.most_common(20)),
            "Top 20 Keys by Frequency"
        )
    else:
        console.print("[yellow]No keys found for histogram[/yellow]")
    
    console.print()
    
    # Display value histogram
    if value_counts:
        display.display_histogram(
            dict(value_counts.most_common(20)),
            "Top 20 Values by Frequency"
        )
    else:
        console.print("[yellow]No values found for histogram[/yellow]")


@app.command()
def version():
    """Show version information."""
    from fuzzygrep import __version__
    console.print(f"[bold cyan]fuzzygrep[/bold cyan] version [green]{__version__}[/green]")


@app.command()
def cache_clear():
    """Clear all cached data."""
    from fuzzygrep.core.cache import CacheManager
    
    try:
        cache_manager = CacheManager()
        cache_manager.clear_all()
        console.print("[green]Cache cleared successfully![/green]")
    except Exception as e:
        console.print(f"[red]Error clearing cache:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def cache_stats():
    """Show cache statistics."""
    from fuzzygrep.core.cache import CacheManager
    
    try:
        cache_manager = CacheManager()
        stats = cache_manager.get_cache_stats()
        
        console.print("\n[bold cyan]Cache Statistics[/bold cyan]")
        console.print(f"Status: {'[green]Enabled[/green]' if stats['enabled'] else '[red]Disabled[/red]'}")
        console.print(f"Memory cache: {stats['memory_cache_size']}/{stats['memory_cache_maxsize']} items")
        console.print(f"Disk cache: {stats['disk_cache_count']} files ({stats['disk_cache_size_mb']:.2f} MB)")
        console.print(f"TTL: {stats['ttl']} seconds")
    except Exception as e:
        console.print(f"[red]Error getting cache stats:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
