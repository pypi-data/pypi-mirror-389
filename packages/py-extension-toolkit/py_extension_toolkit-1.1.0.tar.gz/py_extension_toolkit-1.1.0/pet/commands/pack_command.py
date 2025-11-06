"""Pack command for creating extension packages."""

import click
import json
import zipfile
import os
from pathlib import Path
from datetime import datetime


@click.command()
@click.option('--output', '-o', help='Output file path (default: auto-generated)')
@click.option('--exclude', multiple=True, help='Additional files/patterns to exclude')
def pack(output, exclude):
    """Pack the extension into a distributable format."""
    click.echo("📦 Packing extension...")
    
    # Check if we're in an extension project
    if not Path('manifest.json').exists():
        click.echo("❌ No manifest.json found. Make sure you're in an extension project directory.", err=True)
        return
    
    try:
        with open('manifest.json', 'r') as f:
            manifest = json.load(f)
    except Exception as e:
        click.echo(f"❌ Error reading manifest.json: {e}", err=True)
        return
    
    # Generate output filename if not provided
    if not output:
        name = manifest.get('name', 'extension')
        version = manifest.get('version', '1.0.0')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        suggested_output = f"{name}-{version}-{timestamp}.zip"
        
        click.echo(f"\n📦 Package Configuration")
        if click.confirm(f'💾 Save as "{suggested_output}"?', default=True):
            output = suggested_output
        else:
            output = click.prompt('📁 Output filename', default=f"{name}-{version}.zip")
    
    # Default exclusions
    default_excludes = {
        '__pycache__',
        '*.pyc',
        '.git',
        '.gitignore',
        '.DS_Store',
        'Thumbs.db',
        'node_modules',
        '.env',
        '.venv',
        'venv',
        '*.log',
        '.pytest_cache',
        '.coverage',
        'dist',
        'build',
        '*.egg-info',
        '*.zip'  # Exclude all zip files to prevent recursive inclusion
    }
    
    # Add user-specified exclusions
    all_excludes = default_excludes.union(set(exclude))
    
    created_files = []
    
    try:
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add all files except excluded ones
            for root, dirs, files in os.walk('.'):
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if not should_exclude(d, all_excludes)]
                
                for file in files:
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to('.')
                    
                    # Skip the output file itself to prevent recursive inclusion
                    if str(relative_path) != output and not should_exclude(str(relative_path), all_excludes):
                        zf.write(file_path, relative_path)
                        created_files.append(str(relative_path))
        
        # Get file size
        file_size = Path(output).stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        click.echo("✅ Extension packed successfully!")
        click.echo(f"📁 Output file: {output}")
        click.echo(f"📊 File size: {file_size_mb:.2f} MB")
        click.echo(f"📋 Files included: {len(created_files)}")
        
        if click.confirm("Show included files?"):
            for file_path in sorted(created_files):
                click.echo(f"  📄 {file_path}")
    
    except Exception as e:
        click.echo(f"❌ Error packing extension: {e}", err=True)


def should_exclude(path, excludes):
    """Check if a path should be excluded based on patterns."""
    path_str = str(path).replace('\\\\', '/')
    
    for exclude_pattern in excludes:
        # Simple pattern matching
        if exclude_pattern.startswith('*.'):
            # File extension pattern
            if path_str.endswith(exclude_pattern[1:]):
                return True
        elif exclude_pattern in path_str:
            # Simple substring match
            return True
        elif path_str.startswith(exclude_pattern):
            # Prefix match
            return True
    
    return False