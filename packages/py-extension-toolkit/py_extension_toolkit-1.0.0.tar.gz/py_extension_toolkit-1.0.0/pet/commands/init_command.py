"""Initialize command for creating new extension projects."""

import click
import os
import json
from pathlib import Path


@click.command()
@click.option('--name', help='Name of the extension')
@click.option('--type', 'project_type', type=click.Choice(['web', 'python']), 
              help='Type of extension project')
@click.option('--framework', type=click.Choice(['vanilla', 'react', 'vue']), 
              help='Frontend framework (for web projects)')
def init(name, project_type, framework):
    """Create a new extension project."""
    
    # Interactive prompts if not provided
    if not project_type:
        click.echo('\n? Select the type of extension project:')
        project_types = [
            'Web Extension (Node.js/Express)',
            'Python Extension (Flask)',
            'API Integration',
            'Microservice',
            'Dashboard Extension',
            'Data Connector',
            'Webhook Handler',
            'Custom Widget',
            'Background Service',
            'CLI Tool'
        ]
        
        for i, ptype in enumerate(project_types, 1):
            click.echo(f'  {ptype}')
        
        click.echo('(Use arrow keys to navigate - for demo, enter project type)')
        type_choice = click.prompt('Select project type', type=click.Choice(project_types), default='Web Extension (Node.js/Express)')
        
        # Map selection to project type
        if 'Python' in type_choice:
            project_type = 'python'
        else:
            project_type = 'web'  # Default to web for most extension types
        
        service_name = type_choice
    
    if not name:
        name = click.prompt('? Project Name')
    
    # Set default framework for web projects
    if project_type == 'web' and not framework:
        framework = 'vanilla'  # Default to vanilla for web extensions
    elif project_type == 'python':
        framework = None
    
    click.echo(f"\nInitializing project at: {Path.cwd() / name}")
    click.echo(f"🚀 Creating {service_name if 'service_name' in locals() else project_type} extension: {name}")
    
    # Create project directory
    project_dir = Path(name)
    if project_dir.exists():
        click.echo(f"Directory {name} already exists!", err=True)
        return
    
    project_dir.mkdir(parents=True)
    
    if project_type == 'web':
        create_npm_project(project_dir, name, framework, service_name if 'service_name' in locals() else 'Web Extension')
    elif project_type == 'python':
        create_python_project(project_dir, name)
    
    click.echo("Installing NPM dependencies...")
    
    # Install NPM dependencies
    if project_type == 'web':
        install_npm_dependencies(project_dir)
    
    click.echo(f"Project Initialized: {project_dir.absolute()}")
    click.echo("Run the following commands:")
    click.echo(f"cd '{name}'")
    click.echo("pet run")


def create_npm_project(project_dir, name, framework, service):
    """Create an NPM-based extension project like zet."""
    
    # Create package.json
    package_json = {
        "name": name,
        "version": "1.0.0",
        "description": f"{service} extension - {name}",
        "main": "server.js",
        "scripts": {
            "start": "node server.js",
            "dev": "nodemon server.js",
            "build": "echo 'Build script not configured'"
        },
        "dependencies": {
            "express": "^4.18.0",
            "cors": "^2.8.5",
            "express-rate-limit": "^6.0.0",
            "helmet": "^6.0.0"
        },
        "devDependencies": {
            "nodemon": "^2.0.0"
        },
        "keywords": ["extension", "web-app", service.lower().replace(" ", "-")],
        "author": "",
        "license": "MIT",
        "engines": {
            "node": ">=14.0.0"
        }
    }
    
    with open(project_dir / 'package.json', 'w') as f:
        json.dump(package_json, f, indent=2)
    
    # Create server.js (Express server)
    server_content = f'''const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 5000;

// Security middleware
app.use(helmet({{
    contentSecurityPolicy: false, // Disable for development
    crossOriginEmbedderPolicy: false
}}));

// Rate limiting
const limiter = rateLimit({{
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 1000 // limit each IP to 1000 requests per windowMs
}});
app.use(limiter);

// CORS configuration
app.use(cors({{
    origin: true,
    credentials: true
}}));

// Parse JSON bodies
app.use(express.json());
app.use(express.urlencoded({{ extended: true }}));

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));

// API Routes
app.get('/api/health', (req, res) => {{
    res.json({{
        status: 'OK',
        service: '{service}',
        extension: '{name}',
        version: '1.0.0',
        timestamp: new Date().toISOString()
    }});
}});

app.get('/api/extension-info', (req, res) => {{
    res.json({{
        name: '{name}',
        service: '{service}',
        version: '1.0.0',
        description: '{service} extension - {name}',
        author: 'Extension Developer'
    }});
}});

// Catch all handler: send back index.html
app.get('*', (req, res) => {{
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
}});

// Error handling middleware
app.use((err, req, res, next) => {{
    console.error(err.stack);
    res.status(500).json({{
        error: 'Something went wrong!',
        message: process.env.NODE_ENV === 'development' ? err.message : 'Internal server error'
    }});
}});

// Start server
app.listen(PORT, '127.0.0.1', () => {{
    console.log(`🚀 {service} Extension running at https://127.0.0.1:${{PORT}}`);
    console.log(`Note: Please enable the host (https://127.0.0.1:${{PORT}}) in a new tab and authorize the connection by clicking Advanced->Proceed to 127.0.0.1 (unsafe).`);
}});

module.exports = app;
'''
    
    with open(project_dir / 'server.js', 'w') as f:
        f.write(server_content)
    
    # Create public directory structure
    (project_dir / 'public').mkdir()
    (project_dir / 'public' / 'css').mkdir()
    (project_dir / 'public' / 'js').mkdir()
    (project_dir / 'public' / 'assets').mkdir()
    
    # Create index.html
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - {service} Extension</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="icon" type="image/x-icon" href="assets/favicon.ico">
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>{name}</h1>
            <p class="service-badge">{service} Extension</p>
        </header>
        
        <main class="main-content">
            <div class="welcome-section">
                <h2>Welcome to your {service} Extension!</h2>
                <p>Your extension is ready for development.</p>
            </div>
            
            <div class="features-section">
                <h3>Features</h3>
                <ul>
                    <li>Express.js server with CORS support</li>
                    <li>Security middleware (Helmet, Rate limiting)</li>
                    <li>API endpoints for extension data</li>
                    <li>Static file serving</li>
                    <li>Development-ready structure</li>
                </ul>
            </div>
            
            <div class="api-section">
                <h3>API Endpoints</h3>
                <ul>
                    <li><code>GET /api/health</code> - Health check</li>
                    <li><code>GET /api/extension-info</code> - Extension information</li>
                </ul>
            </div>
            
            <div class="actions-section">
                <button id="healthCheck" class="btn btn-primary">Check Health</button>
                <button id="extensionInfo" class="btn btn-secondary">Extension Info</button>
            </div>
            
            <div id="output" class="output-section"></div>
        </main>
        
        <footer class="footer">
            <p>Built with Python Extension Toolkit (PET) • {service} Extension</p>
        </footer>
    </div>
    
    <script src="js/main.js"></script>
</body>
</html>'''
    
    with open(project_dir / 'public' / 'index.html', 'w') as f:
        f.write(html_content)
    
    # Create CSS
    css_content = '''* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background-color: #f8fafc;
    color: #1a202c;
    line-height: 1.6;
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}}

.header {{
    text-align: center;
    margin-bottom: 40px;
    padding: 40px 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}}

.header h1 {{
    font-size: 2.5rem;
    margin-bottom: 10px;
    font-weight: 700;
}}

.service-badge {{
    display: inline-block;
    background: rgba(255, 255, 255, 0.2);
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 500;
}}

.main-content {{
    display: grid;
    gap: 30px;
}}

.welcome-section,
.features-section,
.api-section,
.actions-section {{
    background: white;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    border: 1px solid #e2e8f0;
}}

.welcome-section h2,
.features-section h3,
.api-section h3 {{
    color: #2d3748;
    margin-bottom: 15px;
    font-weight: 600;
}}

.features-section ul,
.api-section ul {{
    list-style: none;
    padding-left: 0;
}}

.features-section li,
.api-section li {{
    padding: 8px 0;
    border-bottom: 1px solid #f1f5f9;
    position: relative;
    padding-left: 20px;
}}

.features-section li:before {{
    content: '✓';
    color: #48bb78;
    font-weight: bold;
    position: absolute;
    left: 0;
}}

.api-section code {{
    background: #f7fafc;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 0.9rem;
    color: #2d3748;
    border: 1px solid #e2e8f0;
}}

.actions-section {{
    text-align: center;
}}

.btn {{
    display: inline-block;
    padding: 12px 24px;
    margin: 0 8px;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
}}

.btn-primary {{
    background: #4299e1;
    color: white;
}}

.btn-primary:hover {{
    background: #3182ce;
    transform: translateY(-1px);
}}

.btn-secondary {{
    background: #718096;
    color: white;
}}

.btn-secondary:hover {{
    background: #4a5568;
    transform: translateY(-1px);
}}

.output-section {{
    margin-top: 20px;
    padding: 20px;
    background: #f7fafc;
    border-radius: 8px;
    border-left: 4px solid #4299e1;
    display: none;
}}

.output-section.visible {{
    display: block;
}}

.output-section pre {{
    background: #2d3748;
    color: #e2e8f0;
    padding: 15px;
    border-radius: 6px;
    overflow-x: auto;
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 0.9rem;
}}

.footer {{
    text-align: center;
    margin-top: 40px;
    padding: 20px;
    color: #718096;
    font-size: 0.9rem;
}}

@media (max-width: 768px) {{
    .container {{
        padding: 10px;
    }}
    
    .header h1 {{
        font-size: 2rem;
    }}
    
    .btn {{
        display: block;
        margin: 10px 0;
        width: 100%;
    }}
}}'''
    
    with open(project_dir / 'public' / 'css' / 'style.css', 'w') as f:
        f.write(css_content)
    
    # Create JavaScript
    js_content = '''document.addEventListener('DOMContentLoaded', function() {
    const healthCheckBtn = document.getElementById('healthCheck');
    const extensionInfoBtn = document.getElementById('extensionInfo');
    const outputSection = document.getElementById('output');
    
    // Helper function to display output
    function showOutput(title, data) {
        outputSection.innerHTML = `
            <h4>${title}</h4>
            <pre>${JSON.stringify(data, null, 2)}</pre>
        `;
        outputSection.classList.add('visible');
    }
    
    // Health check functionality
    healthCheckBtn.addEventListener('click', async function() {
        try {
            this.textContent = 'Checking...';
            this.disabled = true;
            
            const response = await fetch('/api/health');
            const data = await response.json();
            
            showOutput('Health Check Result', data);
        } catch (error) {
            showOutput('Health Check Error', {
                error: 'Failed to fetch health status',
                message: error.message
            });
        } finally {
            this.textContent = 'Check Health';
            this.disabled = false;
        }
    });
    
    // Extension info functionality
    extensionInfoBtn.addEventListener('click', async function() {
        try {
            this.textContent = 'Loading...';
            this.disabled = true;
            
            const response = await fetch('/api/extension-info');
            const data = await response.json();
            
            showOutput('Extension Information', data);
        } catch (error) {
            showOutput('Extension Info Error', {
                error: 'Failed to fetch extension info',
                message: error.message
            });
        } finally {
            this.textContent = 'Extension Info';
            this.disabled = false;
        }
    });
    
    console.log('Extension loaded successfully');
    console.log('Available API endpoints:');
    console.log('- GET /api/health');
    console.log('- GET /api/extension-info');
});'''
    
    with open(project_dir / 'public' / 'js' / 'main.js', 'w') as f:
        f.write(js_content)
    
    # Create .gitignore
    gitignore_content = '''# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
logs
*.log

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo

# Build outputs
dist/
build/
'''
    
    with open(project_dir / '.gitignore', 'w') as f:
        f.write(gitignore_content)
    
    # Create README.md
    readme_content = f'''# {name}

{service} Extension built with Python Extension Toolkit (PET)

## Description

This is a {service} extension that provides [describe your extension functionality here].

## Features

- Express.js server with CORS support
- Security middleware (Helmet, Rate limiting)
- API endpoints for extension data
- Static file serving
- Development-ready structure

## Getting Started

### Prerequisites

- Node.js (>=14.0.0)
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm start

# Or use nodemon for auto-restart
npm run dev
```

### Development

The extension runs on `https://127.0.0.1:5000` by default.

**Note**: You may need to authorize the self-signed certificate in your browser by clicking "Advanced" → "Proceed to 127.0.0.1 (unsafe)".

### API Endpoints

- `GET /api/health` - Health check endpoint
- `GET /api/extension-info` - Extension information

### Project Structure

```
{name}/
├── public/           # Static files served by Express
│   ├── css/         # Stylesheets
│   ├── js/          # Client-side JavaScript
│   ├── assets/      # Images, icons, etc.
│   └── index.html   # Main HTML file
├── server.js        # Express server
├── package.json     # Node.js dependencies and scripts
└── README.md        # This file
```

### Customization

1. Edit `public/index.html` for the main interface
2. Modify `public/css/style.css` for styling
3. Update `public/js/main.js` for client-side functionality
4. Add server-side logic in `server.js`

### Deployment

Before deploying to production:

1. Set `NODE_ENV=production`
2. Configure proper HTTPS certificates
3. Update CORS settings for your domain
4. Review security middleware settings

## Built With

- Express.js - Web framework
- PET (Python Extension Toolkit) - Project scaffolding
- {service} - Target platform

## License

MIT License - see LICENSE file for details
'''
    
    with open(project_dir / 'README.md', 'w') as f:
        f.write(readme_content)


def create_python_project(project_dir, name):
    """Create a Python-based extension project."""
    # Create basic structure
    (project_dir / 'src').mkdir()
    (project_dir / 'templates').mkdir()
    (project_dir / 'static').mkdir()
    
    # Create manifest.json
    manifest = {
        "name": name,
        "version": "1.0.0",
        "description": f"{name} extension",
        "type": "python",
        "entry_point": "src/main.py",
        "requirements": ["flask>=2.0.0", "flask-cors>=4.0.0"],
        "icon": "static/icon.png"
    }
    
    with open(project_dir / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Create main.py
    python_content = f'''"""
{name} Extension
Main application entry point
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    """Main page of the extension."""
    return render_template('index.html', title='{name}')


@app.route('/api/status')
def status():
    """API endpoint to check extension status."""
    return jsonify({{
        'status': 'active',
        'extension': '{name}',
        'version': '1.0.0'
    }})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
'''
    
    with open(project_dir / 'src' / 'main.py', 'w') as f:
        f.write(python_content)
    
    # Create HTML template
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{{{ title }}}}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; text-align: center; }}
        .status {{ padding: 10px; background: #e8f5e8; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to {name}</h1>
        <div class="status">
            <p>Extension Status: <strong>Active</strong></p>
        </div>
        <p>Your Python extension is running successfully!</p>
        <button onclick="checkStatus()">Check API Status</button>
    </div>
    
    <script>
        async function checkStatus() {{
            try {{
                const response = await fetch('/api/status');
                const data = await response.json();
                alert('Status: ' + data.status + '\\nExtension: ' + data.extension);
            }} catch (error) {{
                alert('Error checking status: ' + error.message);
            }}
        }}
    </script>
</body>
</html>"""
    
    with open(project_dir / 'templates' / 'index.html', 'w') as f:
        f.write(html_template)
    
    # Create requirements.txt
    requirements = """flask>=2.0.0
flask-cors>=4.0.0"""
    
    with open(project_dir / 'requirements.txt', 'w') as f:
        f.write(requirements)


def install_npm_dependencies(project_dir):
    """Install NPM dependencies for the project."""
    import subprocess
    import sys
    
    try:
        # Check if npm is available
        subprocess.run(['npm', '--version'], capture_output=True, check=True, cwd=project_dir)
        
        # Install dependencies
        result = subprocess.run(['npm', 'install'], capture_output=True, text=True, cwd=project_dir)
        
        if result.returncode == 0:
            click.echo("✅ NPM dependencies installed successfully")
        else:
            click.echo("⚠️ NPM install completed with warnings")
            if result.stderr:
                click.echo(f"Warnings: {result.stderr}")
                
    except subprocess.CalledProcessError:
        click.echo("❌ NPM not found. Please install Node.js and npm first.")
        click.echo("Visit: https://nodejs.org/")
    except Exception as e:
        click.echo(f"⚠️ Error installing dependencies: {e}")
        click.echo("You can manually run 'npm install' in the project directory.")