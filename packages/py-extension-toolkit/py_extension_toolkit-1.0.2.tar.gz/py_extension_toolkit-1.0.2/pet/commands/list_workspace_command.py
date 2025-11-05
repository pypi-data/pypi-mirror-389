"""List workspace command for managing workspaces."""

import click
import json
import os
from pathlib import Path
from .login_command import is_authenticated, get_session


@click.command('list-workspace')
def list_workspace():
    """List all workspaces and extensions."""
    
    click.echo("📋 Listing workspaces and extensions...")
    
    # List local extensions (directories with manifest.json)
    click.echo("\\n🏠 Local Extensions:")
    local_extensions = find_local_extensions()
    
    if local_extensions:
        for ext_path, manifest in local_extensions:
            name = manifest.get('name', 'Unknown')
            version = manifest.get('version', 'Unknown')
            ext_type = manifest.get('type', 'web')
            click.echo(f"  📦 {name} (v{version}) - {ext_type}")
            click.echo(f"      📁 {ext_path}")
    else:
        click.echo("  ℹ️ No local extensions found")
    
    # List remote workspaces if authenticated
    if is_authenticated():
        click.echo("\\n☁️ Remote Workspaces:")
        list_remote_workspaces()
    else:
        click.echo("\\n☁️ Remote Workspaces:")
        click.echo("  ❌ Not authenticated. Run 'pet login' to see remote workspaces.")


def find_local_extensions(search_dir="."):
    """Find all local extension projects."""
    extensions = []
    search_path = Path(search_dir)
    
    # Search current directory and subdirectories
    for item in search_path.rglob("manifest.json"):
        try:
            with open(item, 'r') as f:
                manifest = json.load(f)
            extensions.append((item.parent, manifest))
        except (json.JSONDecodeError, IOError):
            continue
    
    return extensions


def list_remote_workspaces():
    """List remote workspaces (demo implementation)."""
    session = get_session()
    
    click.echo(f"  🌐 Server: {session['server']}")
    click.echo(f"  👤 User: {session['username']}")
    
    # Simulate remote workspace listing
    demo_workspaces = [
        {
            "name": "my-workspace",
            "extensions": [
                {"name": "calculator-app", "version": "1.2.0", "type": "web"},
                {"name": "todo-manager", "version": "2.1.5", "type": "python"},
            ]
        },
        {
            "name": "team-workspace", 
            "extensions": [
                {"name": "dashboard", "version": "1.0.0", "type": "web"},
                {"name": "reporting-tool", "version": "1.5.2", "type": "python"},
            ]
        }
    ]
    
    for workspace in demo_workspaces:
        click.echo(f"\\n  📂 Workspace: {workspace['name']}")
        for ext in workspace['extensions']:
            click.echo(f"    📦 {ext['name']} (v{ext['version']}) - {ext['type']}")
    
    # In real implementation, you would:
    # 1. Make API call to get user's workspaces
    # 2. Handle authentication
    # 3. Parse and display actual data
    
    '''
    Real implementation would look like:
    
    try:
        headers = {'Authorization': f'Bearer {session["token"]}'}
        response = requests.get(
            f'{session["server"]}/api/workspaces',
            headers=headers
        )
        
        if response.status_code == 200:
            workspaces = response.json()
            
            for workspace in workspaces:
                click.echo(f"\\n  📂 Workspace: {workspace['name']}")
                
                # Get extensions in workspace
                ext_response = requests.get(
                    f'{session["server"]}/api/workspaces/{workspace["id"]}/extensions',
                    headers=headers
                )
                
                if ext_response.status_code == 200:
                    extensions = ext_response.json()
                    for ext in extensions:
                        click.echo(f"    📦 {ext['name']} (v{ext['version']}) - {ext['type']}")
                else:
                    click.echo("    ❌ Could not load extensions")
        else:
            click.echo(f"  ❌ Failed to load workspaces: {response.text}")
            
    except requests.RequestException as e:
        click.echo(f"  ❌ Network error: {e}")
    except Exception as e:
        click.echo(f"  ❌ Error listing workspaces: {e}")
    '''