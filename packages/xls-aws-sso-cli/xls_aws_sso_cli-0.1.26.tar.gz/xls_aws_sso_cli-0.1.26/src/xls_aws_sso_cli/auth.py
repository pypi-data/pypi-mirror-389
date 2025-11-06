import os
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
import getpass

console = Console()

class AuthManager:
    def __init__(self):
        self.config_dir = Path.home() / ".xls-sso"
        self.config_file = self.config_dir / "credentials.json"
        self.config_dir.mkdir(exist_ok=True)
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        if not self.config_file.exists():
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                creds = json.load(f)
                return creds.get('authenticated', False)
        except:
            return False
    
    def get_credentials(self) -> Optional[dict]:
        """Get stored credentials"""
        if not self.config_file.exists():
            return None
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def login(self, username: str, password: str, token: Optional[str] = None) -> bool:
        """Store credentials and authenticate"""
        try:
            credentials = {
                'username': username,
                'authenticated': True,
                'token': token
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            
            # Set file permissions to be readable only by owner
            os.chmod(self.config_file, 0o600)
            return True
        except Exception as e:
            console.print(f"[red]❌ Login failed: {e}[/red]")
            return False
    
    def logout(self) -> bool:
        """Remove stored credentials"""
        try:
            if self.config_file.exists():
                self.config_file.unlink()
            return True
        except Exception as e:
            console.print(f"[red]❌ Logout failed: {e}[/red]")
            return False
    
    def get_username(self) -> Optional[str]:
        """Get stored username"""
        creds = self.get_credentials()
        return creds.get('username') if creds else None
    
    def get_token(self) -> Optional[str]:
        """Get stored JWT token"""
        creds = self.get_credentials()
        return creds.get('token') if creds else None
    
    def update_token(self, token: str) -> bool:
        """Update JWT token"""
        creds = self.get_credentials()
        if creds:
            creds['token'] = token
            try:
                with open(self.config_file, 'w') as f:
                    json.dump(creds, f, indent=2)
                return True
            except:
                return False
        return False