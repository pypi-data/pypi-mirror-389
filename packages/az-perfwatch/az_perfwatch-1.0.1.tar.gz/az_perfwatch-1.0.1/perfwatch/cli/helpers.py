from rich.console import Console
from rich.table import Table

console = Console()

def print_rich_table(data, headers):
    table = Table(show_header=True, header_style="bold magenta")
    for h in headers:
        table.add_column(h)
    for row in data:
        table.add_row(*[str(row[h.lower()]) for h in headers])
    console.print(table)
