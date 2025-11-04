"""Validate command for checking extension projects."""

import click
import json
import os
from pathlib import Path


@click.command()
@click.option('--strict', is_flag=True, help='Enable strict validation')
def validate(strict):
    """Validate the current extension project."""
    click.echo("🔍 Validating extension project...")
    
    errors = []
    warnings = []
    
    # Check manifest.json
    manifest_path = Path('manifest.json')
    if not manifest_path.exists():
        errors.append("manifest.json is missing")
        click.echo("❌ Validation failed!")
        return
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in manifest.json: {e}")
        click.echo("❌ Validation failed!")
        return
    
    # Validate required fields
    required_fields = ['name', 'version', 'type']
    for field in required_fields:
        if field not in manifest:
            errors.append(f"Required field '{field}' missing in manifest.json")
    
    # Check entry point
    entry_point = manifest.get('entry_point')
    if entry_point and not Path(entry_point).exists():
        errors.append(f"Entry point file not found: {entry_point}")
    
    # Type-specific validation
    extension_type = manifest.get('type', 'web')
    
    if extension_type == 'web':
        validate_web_extension(manifest, errors, warnings, strict)
    elif extension_type == 'python':
        validate_python_extension(manifest, errors, warnings, strict)
    
    # Report results
    if errors:
        click.echo("❌ Validation failed!")
        for error in errors:
            click.echo(f"  ❌ {error}")
    else:
        click.echo("✅ Validation passed!")
    
    if warnings:
        click.echo("⚠️ Warnings:")
        for warning in warnings:
            click.echo(f"  ⚠️ {warning}")
    
    return len(errors) == 0


def validate_web_extension(manifest, errors, warnings, strict):
    """Validate web extension specific requirements."""
    entry_point = manifest.get('entry_point', 'app/index.html')
    
    if not Path(entry_point).exists():
        errors.append(f"Web entry point not found: {entry_point}")
    
    # Check for assets directory
    if not Path('assets').exists():
        warnings.append("Assets directory not found")
    
    # Check for CSS and JS files
    css_dir = Path('assets/css')
    js_dir = Path('assets/js')
    
    if css_dir.exists() and not list(css_dir.glob('*.css')):
        warnings.append("No CSS files found in assets/css")
    
    if js_dir.exists() and not list(js_dir.glob('*.js')):
        warnings.append("No JavaScript files found in assets/js")


def validate_python_extension(manifest, errors, warnings, strict):
    """Validate Python extension specific requirements."""
    entry_point = manifest.get('entry_point', 'src/main.py')
    
    if not Path(entry_point).exists():
        errors.append(f"Python entry point not found: {entry_point}")
    
    # Check for requirements.txt
    if not Path('requirements.txt').exists():
        warnings.append("requirements.txt not found")
    
    # Check Python syntax if strict mode
    if strict and Path(entry_point).exists():
        try:
            with open(entry_point, 'r') as f:
                code = f.read()
            compile(code, entry_point, 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error in {entry_point}: {e}")
    
    # Check for templates directory if Flask is used
    requirements_file = Path('requirements.txt')
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            requirements = f.read()
            if 'flask' in requirements.lower() and not Path('templates').exists():
                warnings.append("Flask detected but templates directory not found")