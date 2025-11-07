"""Enhanced display and visualization with export functionality."""

import csv
import json
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from fuzzygrep.utils.logging import get_logger

logger = get_logger()


class ResultsDisplay:
    """Display search results with rich formatting."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def display_matches(
        self,
        matches: list[tuple[str, float]],
        search_type: str,
        searcher: Any,
        use_pager: bool = True
    ):
        """Display search matches in a formatted table."""
        if not matches:
            self.console.print("[yellow]No matches found.[/yellow]")
            return
        
        table = self._create_results_table(matches, search_type, searcher)
        
        # Use pager for large result sets
        if use_pager and len(matches) > 20:
            with self.console.pager():
                self.console.print(table)
        else:
            self.console.print(table)
    
    def _create_results_table(
        self,
        matches: list[tuple[str, float]],
        search_type: str,
        searcher: Any
    ) -> Table:
        """Create a formatted table for search results."""
        table = Table(
            title=f"[bold cyan]Search Results[/bold cyan] ({len(matches)} matches)",
            show_header=True,
            header_style="bold magenta"
        )
        
        if search_type == "keys":
            table.add_column("Key", style="cyan", no_wrap=False, max_width=50)
            table.add_column("Value", style="green", no_wrap=False, max_width=50)
            table.add_column("Score", style="yellow", justify="right", width=8)
            
            for match, score in matches:
                values = searcher.get_values_for_key(match)
                if values:
                    for value in values[:3]:  # Limit to first 3 values
                        value_str = str(value)
                        if len(value_str) > 100:
                            value_str = value_str[:97] + "..."
                        table.add_row(match, value_str, f"{score:.1f}")
                    
                    if len(values) > 3:
                        table.add_row(
                            "",
                            f"[dim]... and {len(values) - 3} more values[/dim]",
                            ""
                        )
        else:  # search_type == "values"
            table.add_column("Value", style="green", no_wrap=False, max_width=50)
            table.add_column("Keys", style="cyan", no_wrap=False, max_width=50)
            table.add_column("Score", style="yellow", justify="right", width=8)
            
            for match, score in matches:
                keys = searcher.get_keys_for_value(match)
                if keys:
                    keys_str = ", ".join(keys[:5])
                    if len(keys) > 5:
                        keys_str += f" [dim](+{len(keys) - 5} more)[/dim]"
                    table.add_row(match, keys_str, f"{score:.1f}")
        
        return table
    
    def display_tree(
        self,
        data: Any,
        name: str = "root",
        max_items: int = 100
    ):
        """Display data as a rich tree structure."""
        tree = self._generate_tree(data, name=name, max_items=max_items)
        self.console.print(tree)
    
    def _generate_tree(
        self,
        data: Any,
        parent_tree: Optional[Tree] = None,
        name: str = "root",
        max_items: int = 100
    ) -> Tree:
        """Generate a rich tree for visualization."""
        if parent_tree is None:
            tree = Tree(f"[bold cyan]{name}[/bold cyan]")
        else:
            tree = parent_tree.add(f"[cyan]{name}[/cyan]")
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    self._generate_tree(value, parent_tree=tree, name=str(key), max_items=max_items)
                else:
                    tree.add(f"{key}: [green]{value}[/green]")
        
        elif isinstance(data, list):
            items_to_show = data if max_items == 0 else data[:max_items]
            for i, item in enumerate(items_to_show):
                if isinstance(item, (dict, list)):
                    self._generate_tree(item, parent_tree=tree, name=f"[{i}]", max_items=max_items)
                else:
                    tree.add(f"- [green]{item}[/green]")
            
            if max_items > 0 and len(data) > max_items:
                tree.add(f"[dim]... and {len(data) - max_items} more items[/dim]")
        
        return tree
    
    def display_json(self, data: Any, max_lines: int = 100):
        """Display JSON with syntax highlighting."""
        json_str = json.dumps(data, indent=2)
        lines = json_str.split('\n')
        
        if len(lines) > max_lines:
            truncated = '\n'.join(lines[:max_lines])
            truncated += f"\n... ({len(lines) - max_lines} more lines)"
            json_str = truncated
        
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        self.console.print(syntax)
    
    def display_histogram(self, data: dict[str, int], title: str, max_items: int = 20):
        """Display a simple histogram of data."""
        from rich.bar import Bar
        
        self.console.print(f"\n[bold cyan]{title}[/bold cyan]")
        
        # Sort by count descending
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)[:max_items]
        
        if not sorted_items:
            self.console.print("[yellow]No data to display[/yellow]")
            return
        
        # Calculate max value for scaling
        max_value = max(count for _, count in sorted_items)
        
        # Display bars
        for name, count in sorted_items:
            # Truncate long names
            display_name = name if len(name) <= 30 else name[:27] + "..."
            
            # Calculate bar width (max 50 chars)
            bar_width = int((count / max_value) * 50) if max_value > 0 else 0
            bar = "█" * bar_width
            
            self.console.print(f"{display_name:30} {bar} {count}")


class ResultsExporter:
    """Export search results to various formats."""
    
    @staticmethod
    def export_to_json(
        matches: list[tuple[str, float]],
        search_type: str,
        searcher: Any,
        output_path: Path
    ):
        """Export results to JSON format."""
        results = []
        
        for match, score in matches:
            if search_type == "keys":
                values = searcher.get_values_for_key(match)
                results.append({
                    "key": match,
                    "values": values,
                    "score": score
                })
            else:
                keys = searcher.get_keys_for_value(match)
                results.append({
                    "value": match,
                    "keys": keys,
                    "score": score
                })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(results)} results to {output_path}")
    
    @staticmethod
    def export_to_csv(
        matches: list[tuple[str, float]],
        search_type: str,
        searcher: Any,
        output_path: Path
    ):
        """Export results to CSV format."""
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            if search_type == "keys":
                writer = csv.writer(f)
                writer.writerow(["Key", "Value", "Score"])
                
                for match, score in matches:
                    values = searcher.get_values_for_key(match)
                    for value in values:
                        writer.writerow([match, str(value), score])
            else:
                writer = csv.writer(f)
                writer.writerow(["Value", "Keys", "Score"])
                
                for match, score in matches:
                    keys = searcher.get_keys_for_value(match)
                    writer.writerow([match, ", ".join(keys), score])
        
        logger.info(f"Exported {len(matches)} results to {output_path}")
    
    @staticmethod
    def export_to_markdown(
        matches: list[tuple[str, float]],
        search_type: str,
        searcher: Any,
        output_path: Path
    ):
        """Export results to Markdown format."""
        lines = ["# Search Results\n"]
        
        if search_type == "keys":
            lines.append("| Key | Value | Score |")
            lines.append("|-----|-------|-------|")
            
            for match, score in matches:
                values = searcher.get_values_for_key(match)
                for value in values[:5]:  # Limit values
                    value_str = str(value).replace("|", "\\|")
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    lines.append(f"| {match} | {value_str} | {score:.1f} |")
        else:
            lines.append("| Value | Keys | Score |")
            lines.append("|-------|------|-------|")
            
            for match, score in matches:
                keys = searcher.get_keys_for_value(match)
                keys_str = ", ".join(keys[:5])
                if len(keys) > 5:
                    keys_str += f" (+{len(keys) - 5} more)"
                lines.append(f"| {match} | {keys_str} | {score:.1f} |")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Exported {len(matches)} results to {output_path}")
    
    @staticmethod
    def export_to_html(
        matches: list[tuple[str, float]],
        search_type: str,
        searcher: Any,
        output_path: Path
    ):
        """Export results to HTML format."""
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<title>Fuzzygrep Search Results</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }",
            "h1 { color: #333; }",
            "table { border-collapse: collapse; width: 100%; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            "th { background: #4CAF50; color: white; padding: 12px; text-align: left; }",
            "td { padding: 10px; border-bottom: 1px solid #ddd; }",
            "tr:hover { background: #f5f5f5; }",
            ".score { text-align: right; font-weight: bold; color: #4CAF50; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Search Results</h1>",
            "<table>",
        ]
        
        if search_type == "keys":
            html.append("<tr><th>Key</th><th>Value</th><th>Score</th></tr>")
            for match, score in matches:
                values = searcher.get_values_for_key(match)
                for value in values[:5]:
                    value_str = str(value).replace('<', '&lt;').replace('>', '&gt;')
                    if len(value_str) > 100:
                        value_str = value_str[:97] + "..."
                    html.append(f"<tr><td>{match}</td><td>{value_str}</td><td class='score'>{score:.1f}</td></tr>")
        else:
            html.append("<tr><th>Value</th><th>Keys</th><th>Score</th></tr>")
            for match, score in matches:
                keys = searcher.get_keys_for_value(match)
                keys_str = ", ".join(keys[:5])
                if len(keys) > 5:
                    keys_str += f" (+{len(keys) - 5} more)"
                html.append(f"<tr><td>{match}</td><td>{keys_str}</td><td class='score'>{score:.1f}</td></tr>")
        
        html.extend([
            "</table>",
            "</body>",
            "</html>"
        ])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html))
        
        logger.info(f"Exported {len(matches)} results to {output_path}")
