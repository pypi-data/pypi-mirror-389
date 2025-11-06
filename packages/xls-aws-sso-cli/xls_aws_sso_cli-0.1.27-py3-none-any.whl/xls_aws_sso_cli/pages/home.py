import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.align import Align
from ..auth import AuthManager

console = Console()

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def show_header():
    """Display header with user info"""
    auth_manager = AuthManager()
    username = auth_manager.get_username()
    
    header = Table.grid(padding=(0, 2))
    header.add_column(style="cyan", justify="left")
    header.add_column(style="green", justify="right")
    
    header.add_row(
        f"[bold white]🔐 XLS AWS SSO CLI[/bold white]",
        f"[bold cyan]👤 {username}[/bold cyan]"
    )
    
    console.print(Panel(header, border_style="cyan", padding=(0, 2)))

def show_menu_options():
    """Display menu options in a beautiful table"""
    table = Table(
        show_header=False,
        border_style="cyan",
        box=None,
        padding=(0, 2)
    )
    
    table.add_column("No", style="bold cyan", width=4)
    table.add_column("Icon", width=3)
    table.add_column("Option", style="bold white", width=30)
    table.add_column("Description", style="dim white")
    
    menu_items = [
        ("1", "🎫", "Get JWT Token", "Fetch authentication token"),
        ("2", "🔐", "Interactive Login", "Login and store credentials"),
        ("3", "🔓", "Logout", "Remove stored credentials"),
        ("4", "📊", "Authentication Status", "Check current auth status"),
        ("5", "❓", "Help", "Show detailed help"),
        ("6", "🔄", "Fetch AppInstances", "Fetch and save appinstances"),
        ("7", "📋", "Show AppInstances Table", "Display appinstances as table"),
        ("8", "📋", "SSM Account Menu", "SSM account management"),
        ("9", "📋", "Port Forward Menu", "Port forward management"),
        ("0", "✗", "Exit", "Exit the application"),
    ]
    
    for no, icon, option, desc in menu_items:
        table.add_row(no, icon, option, desc)
    
    return table

def show_main_menu():
    """Display the main menu"""
    clear_screen()
    show_header()
    
    console.print()
    menu_panel = Panel(
        show_menu_options(),
        title="[bold cyan]📋 Main Menu[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(menu_panel)

def handle_menu_choice(choice: str) -> bool:
    """Handle menu selection"""
    auth_manager = AuthManager()
    
    actions = {
        "1": get_jwt_token,
        "2": interactive_login,
        "3": logout,
        "4": show_auth_status,
        "5": show_help,
        "6": fetch_appinstances,
        "7": show_appinstances_table,
        "8": ssm_account_menu,
        "9": port_forward_menu,
        "0": exit_app,
    }
    
    action = actions.get(choice)
    if action:
        return action()
    else:
        console.print("[red]❌ Invalid option. Please try again.[/red]")
        input("\nPress Enter to continue...")
        return True

# Menu action functions
def get_jwt_token():
    clear_screen()
    console.print(Panel(
        "[yellow]🎫 Getting JWT Token...[/yellow]\n\n"
        "[dim]This feature will fetch your authentication token[/dim]",
        title="Get JWT Token",
        border_style="yellow"
    ))
    # Add your JWT token logic here
    input("\n\nPress Enter to continue...")
    return True

def interactive_login():
    clear_screen()
    console.print(Panel(
        "[cyan]🔐 Interactive Login[/cyan]\n\n"
        "[dim]Re-authenticate with new credentials[/dim]",
        title="Interactive Login",
        border_style="cyan"
    ))
    # Add your login logic here
    input("\n\nPress Enter to continue...")
    return True

def logout():
    clear_screen()
    auth_manager = AuthManager()
    
    if Prompt.ask(
        "[yellow]⚠ Are you sure you want to logout?[/yellow]",
        choices=["y", "n"],
        default="n"
    ) == "y":
        if auth_manager.logout():
            console.print("\n[green]✅ Logged out successfully[/green]")
            input("\nPress Enter to exit...")
            return False
    return True

def show_auth_status():
    clear_screen()
    auth_manager = AuthManager()
    
    status_table = Table(show_header=False, border_style="cyan")
    status_table.add_column("Property", style="bold cyan")
    status_table.add_column("Value", style="white")
    
    status_table.add_row("Status", "[green]✅ Authenticated[/green]" if auth_manager.is_authenticated() else "[red]❌ Not Authenticated[/red]")
    status_table.add_row("Username", auth_manager.get_username() or "[dim]N/A[/dim]")
    status_table.add_row("Token", "[green]✓ Present[/green]" if auth_manager.get_token() else "[red]✗ Missing[/red]")
    
    console.print(Panel(
        status_table,
        title="[bold cyan]📊 Authentication Status[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    ))
    input("\n\nPress Enter to continue...")
    return True

def show_help():
    clear_screen()
    console.print(Panel(
        "[bold cyan]XLS AWS SSO CLI - Help[/bold cyan]\n\n"
        "[yellow]Available Commands:[/yellow]\n"
        "• Get JWT Token - Fetch your authentication token\n"
        "• Interactive Login - Re-authenticate with credentials\n"
        "• Logout - Clear stored credentials\n"
        "• Auth Status - View your authentication details\n"
        "• Fetch AppInstances - Get AWS SSO app instances\n"
        "• Show AppInstances - Display instances in table format\n\n"
        "[dim]For more information, visit the documentation[/dim]",
        title="[bold cyan]❓ Help[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    ))
    input("\n\nPress Enter to continue...")
    return True

def fetch_appinstances():
    clear_screen()
    console.print(Panel(
        "[yellow]🔄 Fetching AppInstances...[/yellow]\n\n"
        "[dim]This will fetch and save your AWS SSO app instances[/dim]",
        title="Fetch AppInstances",
        border_style="yellow"
    ))
    # Add your fetch logic here
    input("\n\nPress Enter to continue...")
    return True

def show_appinstances_table():
    clear_screen()
    console.print(Panel(
        "[cyan]📋 AppInstances Table[/cyan]\n\n"
        "[dim]No appinstances found. Use 'Fetch AppInstances' first.[/dim]",
        title="AppInstances",
        border_style="cyan"
    ))
    input("\n\nPress Enter to continue...")
    return True

def ssm_account_menu():
    clear_screen()
    console.print(Panel(
        "[cyan]📋 SSM Account Menu[/cyan]\n\n"
        "[dim]SSM account management features[/dim]",
        title="SSM Account Menu",
        border_style="cyan"
    ))
    input("\n\nPress Enter to continue...")
    return True

def port_forward_menu():
    clear_screen()
    console.print(Panel(
        "[cyan]📋 Port Forward Menu[/cyan]\n\n"
        "[dim]Port forwarding management features[/dim]",
        title="Port Forward Menu",
        border_style="cyan"
    ))
    input("\n\nPress Enter to continue...")
    return True

def exit_app():
    clear_screen()
    console.print(Panel(
        "[bold cyan]👋 Thank you for using XLS AWS SSO CLI[/bold cyan]\n\n"
        "[dim]Goodbye![/dim]",
        title="[bold cyan]Exit[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    ))
    return False

def main_menu_loop():
    """Main menu loop"""
    running = True
    while running:
        show_main_menu()
        choice = Prompt.ask(
            "\n[bold cyan]Select an option[/bold cyan]",
            choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            default="0"
        )
        running = handle_menu_choice(choice)