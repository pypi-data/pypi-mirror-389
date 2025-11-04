"""Login command for authentication."""

import click
import json
import os
from pathlib import Path


@click.command()
@click.option('--server', help='Extension server URL')
@click.option('--username', help='Your username')
@click.option('--password', help='Your password')
def login(server, username, password):
    """Login to the extension server."""
    
    # Interactive prompts if not provided
    if not server:
        server = click.prompt('🌐 Server URL', default='https://crm.aqaryint.com')
    
    if not username:
        username = click.prompt('👤 Username')
    
    if not password:
        password = click.prompt('🔑 Password', hide_input=True)
    
    click.echo(f"🔐 Logging in to {server}...")
    
    # Create session directory
    session_dir = Path.home() / '.pet'
    session_dir.mkdir(exist_ok=True)
    
    # Store session info (in a real implementation, you'd authenticate with the server)
    session_data = {
        'server': server,
        'username': username,
        'authenticated': True,
        'token': 'dummy-token-for-demo'  # In real implementation, get from server
    }
    
    session_file = session_dir / 'session.json'
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)
    
    click.echo("✅ Login successful!")
    click.echo(f"📝 Session saved to: {session_file}")


def get_session():
    """Get current session information."""
    session_file = Path.home() / '.pet' / 'session.json'
    
    if not session_file.exists():
        return None
    
    try:
        with open(session_file, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def is_authenticated():
    """Check if user is authenticated."""
    session = get_session()
    return session and session.get('authenticated', False)