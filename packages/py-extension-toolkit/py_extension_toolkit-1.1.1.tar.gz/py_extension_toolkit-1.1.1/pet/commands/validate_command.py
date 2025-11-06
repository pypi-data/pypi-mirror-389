"""Validate command for checking extension projects."""

import click
import json
from pathlib import Path


@click.command()
@click.option('--strict', is_flag=True, help='Enable strict validation')
def validate(strict):
    """Validate the current extension project."""
    
    errors = []
    warnings = []
    
    # Check manifest.json
    manifest_path = Path('manifest.json')
    if not manifest_path.exists():
        errors.append("manifest.json is missing")
        click.echo("❌ Validation failed!")
        return
    
    # Get project name from manifest for the validation message
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        project_name = manifest.get('name', 'extension')
        click.echo(f"🔍 Validating {project_name} project...")
    except:
        click.echo("🔍 Validating extension project...")
        manifest = {}
    
    # Re-read and validate manifest structure (we already read it above for the project name)
    if not manifest:  # If we couldn't read it above, try again with proper error handling
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:  # Added encoding
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in manifest.json: {e}")
            click.echo("❌ Validation failed!")
            return
        except UnicodeDecodeError as e:
            errors.append(f"Encoding error in manifest.json: {e}")
            click.echo("❌ Validation failed!")
            return
        except IOError as e:
            errors.append(f"Could not read manifest.json: {e}")
            click.echo("❌ Validation failed!")
            return
    
    # Validate required fields
    required_fields = ['name', 'version', 'type']
    for field in required_fields:
        if field not in manifest:
            errors.append(f"Required field '{field}' missing in manifest.json")
        elif not manifest[field]:  # Check for empty values
            errors.append(f"Required field '{field}' is empty in manifest.json")
    
    # Validate field types and values
    if 'name' in manifest and not isinstance(manifest['name'], str):
        errors.append("Field 'name' must be a string")
    
    if 'version' in manifest:
        if not isinstance(manifest['version'], str):
            errors.append("Field 'version' must be a string")
        # Basic semver validation
        elif not manifest['version'].replace('.', '').replace('-', '').replace('+', '').replace('_', '').replace('alpha', '').replace('beta', '').replace('rc', '').isalnum():
            warnings.append("Version format may not follow semantic versioning")
    
    if 'type' in manifest:
        valid_types = ['web', 'python', 'api', 'microservice', 'dashboard', 'connector', 'webhook', 'widget', 'service', 'cli']
        if manifest['type'] not in valid_types:
            warnings.append(f"Extension type '{manifest['type']}' is not a recognized type. Valid types: {', '.join(valid_types)}")
    
    # Check entry point
    entry_point = manifest.get('entry_point')
    if entry_point and not Path(entry_point).exists():
        errors.append(f"Entry point file not found: {entry_point}")
    elif not entry_point:
        warnings.append("No entry_point specified in manifest.json")
    
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
    entry_point = manifest.get('entry_point', 'public/index.html')  # Fixed: should be public/index.html for web extensions
    
    if not Path(entry_point).exists():
        errors.append(f"Web entry point not found: {entry_point}")
    
    # Check for package.json (Node.js projects need this)
    if not Path('package.json').exists():
        warnings.append("package.json not found - Node.js projects should have this file")
    
    # Check for server.js (Express server)
    if not Path('server.js').exists():
        warnings.append("server.js not found - Express projects should have this file")
    
    # Check for public directory structure (updated for new project structure)
    public_dir = Path('public')
    if not public_dir.exists():
        warnings.append("public directory not found")
    else:
        # Check for CSS and JS in public directory
        css_dir = public_dir / 'css'
        js_dir = public_dir / 'js'
        
        if not css_dir.exists():
            warnings.append("public/css directory not found")
        elif not list(css_dir.glob('*.css')):
            warnings.append("No CSS files found in public/css")
        
        if not js_dir.exists():
            warnings.append("public/js directory not found")
        elif not list(js_dir.glob('*.js')):
            warnings.append("No JavaScript files found in public/js")
    
    # Check Node.js dependencies if package.json exists
    package_json_path = Path('package.json')
    if package_json_path.exists():
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            # Check for required dependencies
            dependencies = package_data.get('dependencies', {})
            required_deps = ['express', 'cors']
            
            for dep in required_deps:
                if dep not in dependencies:
                    warnings.append(f"Missing recommended dependency: {dep}")
                    
        except (json.JSONDecodeError, IOError):
            warnings.append("Could not read package.json file")


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
            with open(entry_point, 'r', encoding='utf-8') as f:  # Added encoding
                code = f.read()
            compile(code, entry_point, 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error in {entry_point}: {e}")
        except UnicodeDecodeError as e:
            errors.append(f"Encoding error in {entry_point}: {e}")
        except IOError as e:
            errors.append(f"Could not read {entry_point}: {e}")
    
    # Check for src directory structure
    src_dir = Path('src')
    if not src_dir.exists():
        warnings.append("src directory not found")
    
    # Check for templates directory if Flask is used
    requirements_file = Path('requirements.txt')
    if requirements_file.exists():
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:  # Added encoding and error handling
                requirements = f.read()
                if 'flask' in requirements.lower():
                    if not Path('templates').exists():
                        warnings.append("Flask detected but templates directory not found")
                    if not Path('static').exists():
                        warnings.append("Flask detected but static directory not found")
        except (IOError, UnicodeDecodeError) as e:
            warnings.append(f"Could not read requirements.txt: {e}")
    
    # Check for __init__.py in src directory
    if src_dir.exists() and not (src_dir / '__init__.py').exists():
        warnings.append("src/__init__.py not found - Python packages should have this file")