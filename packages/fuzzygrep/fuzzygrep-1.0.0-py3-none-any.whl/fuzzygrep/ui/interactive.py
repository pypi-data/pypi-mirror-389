"""Enhanced interactive session with improved keyboard shortcuts and UX."""

from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from rapidfuzz import fuzz, process
from rich.console import Console

from fuzzygrep.core.searcher import FuzzySearcher
from fuzzygrep.ui.display import ResultsDisplay, ResultsExporter
from fuzzygrep.utils.logging import get_logger

logger = get_logger()


class FuzzyCompleter(Completer):
    """Autocompleter for fuzzy search."""
    
    def __init__(self, searcher: FuzzySearcher, completion_type: str = "keys"):
        self.searcher = searcher
        self.completion_type = completion_type
    
    def get_completions(self, document, complete_event):
        """Generate completions based on current input."""
        text = document.text_before_cursor
        
        if not text:
            return
        
        # Get candidates based on completion type
        if self.completion_type == "keys":
            candidates = self.searcher.unique_keys
        else:
            candidates = self.searcher.unique_values
        
        # Fuzzy match candidates
        matches = process.extract(
            text,
            candidates,
            scorer=fuzz.WRatio,
            limit=10,
            score_cutoff=60
        )
        
        # process.extract() returns tuples of (match, score, index)
        for match, score, _ in matches:
            yield Completion(
                match,
                start_position=-len(text),
                display_meta=f"score: {score:.0f}"
            )


class CommandCompleter(Completer):
    """Autocompleter for commands."""
    
    COMMANDS = [
        "/exit", "/quit", "/load", "/reload", "/export", "/help",
        "/stats", "/filter", "/clear", "/history", "/save"
    ]
    
    def get_completions(self, document, complete_event):
        """Generate command completions."""
        text = document.text_before_cursor
        
        if not text.startswith('/'):
            return
        
        for cmd in self.COMMANDS:
            if cmd.startswith(text):
                yield Completion(cmd, start_position=-len(text))


class DynamicCompleter(Completer):
    """Dynamic completer that switches between fuzzy and command completion."""
    
    def __init__(self, fuzzy_completer: FuzzyCompleter, command_completer: CommandCompleter):
        self.fuzzy_completer = fuzzy_completer
        self.command_completer = command_completer
    
    def get_completions(self, document, complete_event):
        """Route to appropriate completer based on input."""
        text = document.text_before_cursor
        
        if text.startswith('/'):
            yield from self.command_completer.get_completions(document, complete_event)
        else:
            yield from self.fuzzy_completer.get_completions(document, complete_event)


class InteractiveSession:
    """Enhanced interactive search session with rich UX."""
    
    def __init__(self, searcher: FuzzySearcher):
        self.searcher = searcher
        self.console = Console()
        self.display = ResultsDisplay(self.console)
        
        # Session state
        self.completion_type = "keys"
        self.last_results = []
        self.last_search_type = "keys"
        self.search_history = []
        
        # Setup completers
        self.fuzzy_completer = FuzzyCompleter(searcher, self.completion_type)
        self.command_completer = CommandCompleter()
        self.dynamic_completer = DynamicCompleter(
            self.fuzzy_completer,
            self.command_completer
        )
        
        # Setup key bindings
        self.kb = self._create_key_bindings()
        
        # Create prompt session
        self.session = PromptSession(
            completer=self.dynamic_completer,
            complete_while_typing=True,
            key_bindings=self.kb
        )
    
    def _create_key_bindings(self) -> KeyBindings:
        """Create custom key bindings."""
        kb = KeyBindings()
        
        @kb.add('c-t')
        def _(event):
            """Toggle autocompletion on/off."""
            self.session.complete_while_typing = not self.session.complete_while_typing
            status = "enabled" if self.session.complete_while_typing else "disabled"
            self.console.print(f"[yellow]Autocompletion {status}[/yellow]")
        
        @kb.add('c-v')
        def _(event):
            """Toggle between key and value completion."""
            if self.completion_type == "keys":
                self.completion_type = "values"
                self.console.print("[yellow]Switched to value autocompletion[/yellow]")
            else:
                self.completion_type = "keys"
                self.console.print("[yellow]Switched to key autocompletion[/yellow]")
            
            self.fuzzy_completer.completion_type = self.completion_type
        
        @kb.add('c-r')
        def _(event):
            """Reload data from file."""
            self.console.print("[yellow]Reloading data...[/yellow]")
            self.searcher.reload()
            self.console.print("[green]Data reloaded successfully![/green]")
        
        @kb.add('c-s')
        def _(event):
            """Save last results."""
            if self.last_results:
                self._save_results()
            else:
                self.console.print("[yellow]No results to save[/yellow]")
        
        @kb.add('f1')
        def _(event):
            """Show help."""
            self._show_help()
        
        @kb.add('c-f')
        def _(event):
            """Show filter menu."""
            self.console.print("[yellow]Use /filter <patterns> to filter keys[/yellow]")
        
        return kb
    
    def run(self):
        """Run the interactive session."""
        self._show_welcome()
        
        while True:
            try:
                # Get user input
                prompt_text = f"[{self.searcher.file_path.name}] Search> "
                query = self.session.prompt(prompt_text)
                
                if not query:
                    continue
                
                # Add to history
                if query not in self.search_history:
                    self.search_history.append(query)
                
                # Process command or search
                if query.startswith('/'):
                    self._handle_command(query)
                else:
                    self._handle_search(query)
            
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                self.console.print(f"[red]Error: {e}[/red]")
    
    def _handle_search(self, query: str):
        """Handle search query."""
        # Search both keys and values
        key_matches = self.searcher.search(query, search_type="keys")
        value_matches = self.searcher.search(query, search_type="values")
        
        # Display key matches
        if key_matches:
            self.console.print("\n[bold cyan]Matches in Keys:[/bold cyan]")
            self.display.display_matches(key_matches, "keys", self.searcher, use_pager=False)
            self.last_results = key_matches
            self.last_search_type = "keys"
        
        # Display value matches
        if value_matches:
            self.console.print("\n[bold cyan]Matches in Values:[/bold cyan]")
            self.display.display_matches(value_matches, "values", self.searcher, use_pager=False)
            if not key_matches:
                self.last_results = value_matches
                self.last_search_type = "values"
        
        # No matches found
        if not key_matches and not value_matches:
            self.console.print("[yellow]No matches found.[/yellow]")
            self.console.print("[dim]Try a different query or lower the score threshold.[/dim]")
    
    def _handle_command(self, command: str):
        """Handle command input."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in ["/exit", "/quit"]:
            raise EOFError
        
        elif cmd == "/help":
            self._show_help()
        
        elif cmd == "/load":
            self._load_file(args)
        
        elif cmd == "/reload":
            self.searcher.reload()
            self.console.print("[green]Data reloaded successfully![/green]")
        
        elif cmd == "/export":
            self._export_results(args)
        
        elif cmd == "/stats":
            self._show_stats()
        
        elif cmd == "/filter":
            self._apply_filter(args)
        
        elif cmd == "/clear":
            self.searcher.clear_key_filter()
            self.console.print("[green]Filter cleared[/green]")
        
        elif cmd == "/history":
            self._show_history()
        
        elif cmd == "/save":
            self._save_results()
        
        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")
            self.console.print("[dim]Type /help for available commands[/dim]")
    
    def _show_welcome(self):
        """Show welcome message."""
        stats = self.searcher.get_stats()
        
        self.console.print("\n[bold cyan]Welcome to Fuzzygrep![/bold cyan]")
        self.console.print(f"Loaded: [green]{stats['file_path']}[/green]")
        self.console.print(
            f"Keys: [yellow]{stats['total_keys']}[/yellow] | "
            f"Values: [yellow]{stats['total_values']}[/yellow] | "
            f"Size: [yellow]{stats['file_size_mb']:.2f} MB[/yellow]"
        )
        self.console.print("\n[dim]Type /help for commands or start searching![/dim]\n")
    
    def _show_help(self):
        """Show help message."""
        help_text = """
[bold cyan]Fuzzygrep Commands[/bold cyan]

[bold yellow]Search:[/bold yellow]
  Just type your query to search

[bold yellow]Commands:[/bold yellow]
  /help                 Show this help
  /exit, /quit          Exit the program
  /load <file>          Load a different file
  /reload               Reload current file
  /export <format>      Export results (json/csv/md/html)
  /save                 Quick save to results.json
  /stats                Show statistics
  /filter <patterns>    Filter keys (comma-separated)
  /clear                Clear key filter
  /history              Show search history

[bold yellow]Keyboard Shortcuts:[/bold yellow]
  F1                    Show this help
  Ctrl+T                Toggle autocompletion
  Ctrl+V                Toggle key/value completion
  Ctrl+R                Reload data
  Ctrl+S                Save last results
  Ctrl+C                Exit
        """
        self.console.print(help_text)
    
    def _show_stats(self):
        """Show statistics."""
        stats = self.searcher.get_stats()
        
        self.console.print("\n[bold cyan]Statistics[/bold cyan]")
        self.console.print(f"File: {stats['file_path']}")
        self.console.print(f"Size: {stats['file_size_mb']:.2f} MB")
        self.console.print(f"Keys: {stats['total_keys']}")
        self.console.print(f"Values: {stats['total_values']}")
        self.console.print(f"Cache enabled: {stats['cache_enabled']}")
        self.console.print(f"Index enabled: {stats['index_enabled']}")
        self.console.print(f"Parallel processing: {stats['parallel_enabled']}")
        
        if stats['cache_enabled']:
            cache_stats = stats['cache_stats']
            self.console.print(
                f"\nCache: {cache_stats['memory_cache_size']}/{cache_stats['memory_cache_maxsize']} items, "
                f"{cache_stats['disk_cache_count']} disk caches "
                f"({cache_stats['disk_cache_size_mb']:.2f} MB)"
            )
    
    def _show_history(self):
        """Show search history."""
        if not self.search_history:
            self.console.print("[yellow]No search history[/yellow]")
            return
        
        self.console.print("\n[bold cyan]Search History[/bold cyan]")
        for i, query in enumerate(self.search_history[-10:], 1):
            self.console.print(f"{i}. {query}")
    
    def _load_file(self, file_path: str):
        """Load a different file."""
        if not file_path:
            self.console.print("[red]Usage: /load <file_path>[/red]")
            return
        
        try:
            path = Path(file_path)
            if not path.exists():
                self.console.print(f"[red]File not found: {file_path}[/red]")
                return
            
            self.console.print(f"[yellow]Loading {file_path}...[/yellow]")
            self.searcher = FuzzySearcher(path)
            self.fuzzy_completer.searcher = self.searcher
            self.console.print("[green]File loaded successfully![/green]")
            self._show_welcome()
        
        except Exception as e:
            self.console.print(f"[red]Error loading file: {e}[/red]")
    
    def _apply_filter(self, patterns: str):
        """Apply key filter."""
        if not patterns:
            self.console.print("[red]Usage: /filter <pattern1,pattern2,...>[/red]")
            return
        
        pattern_list = [p.strip() for p in patterns.split(',')]
        self.searcher.set_key_filter(pattern_list)
        self.console.print(f"[green]Filter applied: {', '.join(pattern_list)}[/green]")
    
    def _export_results(self, format_and_path: str):
        """Export results to file."""
        if not self.last_results:
            self.console.print("[yellow]No results to export[/yellow]")
            return
        
        parts = format_and_path.split(maxsplit=1)
        format_type = parts[0].lower() if parts else "json"
        output_path = Path(parts[1]) if len(parts) > 1 else Path(f"results.{format_type}")
        
        try:
            if format_type == "json":
                ResultsExporter.export_to_json(
                    self.last_results, self.last_search_type, self.searcher, output_path
                )
            elif format_type == "csv":
                ResultsExporter.export_to_csv(
                    self.last_results, self.last_search_type, self.searcher, output_path
                )
            elif format_type in ["md", "markdown"]:
                ResultsExporter.export_to_markdown(
                    self.last_results, self.last_search_type, self.searcher, output_path
                )
            elif format_type == "html":
                ResultsExporter.export_to_html(
                    self.last_results, self.last_search_type, self.searcher, output_path
                )
            else:
                self.console.print(f"[red]Unsupported format: {format_type}[/red]")
                self.console.print("[dim]Supported: json, csv, md, html[/dim]")
                return
            
            self.console.print(f"[green]Results exported to {output_path}[/green]")
        
        except Exception as e:
            self.console.print(f"[red]Export error: {e}[/red]")
    
    def _save_results(self):
        """Quick save results to results.json."""
        if not self.last_results:
            self.console.print("[yellow]No results to save[/yellow]")
            return
        
        self._export_results("json results.json")
