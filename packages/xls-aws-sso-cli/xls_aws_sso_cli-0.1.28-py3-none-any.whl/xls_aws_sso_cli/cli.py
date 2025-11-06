import typer
from rich.console import Console
from .pages.login import login_page
from .pages.menu import main_menu_loop
from .auth import AuthManager

console = Console()
app = typer.Typer(help="🔥 XLS AWS SSO CLI - Manage AWS SSO")

@app.callback()
def main_callback():
    """XLS AWS SSO CLI Tool"""
    pass

@app.command()
def start():
    """Start the XLS AWS SSO CLI application"""
    # Check authentication and show login if needed
    if login_page():
        # User authenticated, show main menu
        main_menu_loop()
    else:
        console.print("[red]❌ Authentication failed. Exiting...[/red]")
        raise typer.Exit(code=1)

@app.command()
def logout():
    """Logout from XLS AWS SSO CLI"""
    auth_manager = AuthManager()
    if auth_manager.logout():
        console.print("[green]✅ Logged out successfully[/green]")
    else:
        console.print("[red]❌ Logout failed[/red]")

@app.command()
def status():
    """Show authentication status"""
    auth_manager = AuthManager()
    if auth_manager.is_authenticated():
        console.print(f"[green]✅ Authenticated as: {auth_manager.get_username()}[/green]")
    else:
        console.print("[red]❌ Not authenticated[/red]")

@app.command()
def version():
    """Show version"""
    from . import __version__
    console.print(f"[bold blue]XLS AWS SSO CLI v{__version__}[/bold blue]")

def main():
    """Entry point for the CLI"""
    app()

if __name__ == "__main__":
    main()