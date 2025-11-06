import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="🔥 XLS AWS SSO CLI - Manage AWS SSO")

@app.callback()
def main_callback():
    """XLS AWS SSO CLI Tool"""
    pass

@app.command()
def hello(name: str = "World"):
    """Say hello to someone"""
    console.print(f"[bold green]Hello {name}![/bold green]")

@app.command()
def version():
    """Show version"""
    console.print("[bold blue]XLS AWS SSO CLI v0.1.13[/bold blue]")

def main():
    """Entry point for the CLI"""
    app()

if __name__ == "__main__":
    main()