import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.align import Align
from rich.table import Table
import getpass
from ..auth import AuthManager

console = Console()

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def show_login_banner():
    """Display beautiful login banner"""
    clear_screen()
    
    banner = Text()
    banner.append("\n")
    banner.append("╔═══════════════════════════════════════════════════════╗\n", style="bold cyan")
    banner.append("║                                                       ║\n", style="bold cyan")
    banner.append("║           ", style="bold cyan")
    banner.append("🔐 XLS AWS SSO AUTHENTICATION", style="bold white")
    banner.append("           ║\n", style="bold cyan")
    banner.append("║                                                       ║\n", style="bold cyan")
    banner.append("╚═══════════════════════════════════════════════════════╝\n", style="bold cyan")
    
    console.print(Align.center(banner))
    console.print()

def show_login_form() -> bool:
    """Display login form and authenticate user"""
    show_login_banner()
    
    # Create login form panel
    login_panel = Panel(
        "[bold yellow]Please enter your credentials to continue[/bold yellow]\n\n"
        "[dim]Your credentials will be securely stored locally[/dim]",
        title="[bold cyan]🔑 Login Required[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(Align.center(login_panel))
    console.print()
    
    auth_manager = AuthManager()
    
    try:
        # Get username
        username = Prompt.ask(
            "[bold cyan]👤 Username[/bold cyan]",
            default=""
        )
        
        if not username:
            console.print("[red]❌ Username cannot be empty[/red]")
            return False
        
        # Get password (hidden input)
        console.print("[bold cyan]🔒 Password[/bold cyan]", end=" ")
        password = getpass.getpass("")
        
        if not password:
            console.print("[red]❌ Password cannot be empty[/red]")
            return False
        
        # Simulate authentication (replace with actual auth logic)
        console.print("\n[yellow]⏳ Authenticating...[/yellow]")
        
        # Here you would call your actual authentication API
        # For now, we'll just store the credentials
        if auth_manager.login(username, password):
            console.print("[green]✅ Authentication successful![/green]\n")
            return True
        else:
            console.print("[red]❌ Authentication failed[/red]\n")
            return False
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Login cancelled[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        return False

def login_page() -> bool:
    """Main login page"""
    auth_manager = AuthManager()
    
    # Check if already authenticated
    if auth_manager.is_authenticated():
        clear_screen()
        username = auth_manager.get_username()
        console.print(Panel(
            f"[bold green]✅ Already logged in as:[/bold green] [cyan]{username}[/cyan]\n\n"
            "[dim]Loading main menu...[/dim]",
            title="[bold green]Authentication Status[/bold green]",
            border_style="green",
            padding=(1, 2)
        ))
        return True
    
    # Show login form
    max_attempts = 3
    for attempt in range(max_attempts):
        if show_login_form():
            return True
        
        if attempt < max_attempts - 1:
            console.print(f"\n[yellow]⚠ Attempts remaining: {max_attempts - attempt - 1}[/yellow]\n")
            input("Press Enter to try again...")
    
    console.print("\n[red]❌ Maximum login attempts reached. Exiting...[/red]")
    return False