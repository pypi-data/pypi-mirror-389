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
    if not name:
        name = click.prompt('📦 Extension name')
    
    if not project_type:
        click.echo('\n📋 Select project type:')
        click.echo('  1. Web (HTML/CSS/JavaScript)')
        click.echo('  2. Python (Flask application)')
        
        choice = click.prompt('Choose project type', type=click.Choice(['1', '2', 'web', 'python']), default='1')
        
        if choice in ['1', 'web']:
            project_type = 'web'
        else:
            project_type = 'python'
    
    # Framework selection only for web projects
    if project_type == 'web' and not framework:
        click.echo('\n🎨 Select frontend framework:')
        click.echo('  1. Vanilla (Plain HTML/CSS/JS)')
        click.echo('  2. React (Coming soon)')
        click.echo('  3. Vue (Coming soon)')
        
        fw_choice = click.prompt('Choose framework', type=click.Choice(['1', '2', '3', 'vanilla', 'react', 'vue']), default='1')
        
        if fw_choice in ['1', 'vanilla']:
            framework = 'vanilla'
        elif fw_choice in ['2', 'react']:
            framework = 'react'
        else:
            framework = 'vue'
    elif project_type == 'python':
        framework = None  # Not applicable for Python projects
    
    click.echo(f"\n🚀 Creating {project_type} extension: {name}")
    
    # Create project directory
    project_dir = Path(name)
    if project_dir.exists():
        click.echo(f"Directory {name} already exists!", err=True)
        return
    
    project_dir.mkdir(parents=True)
    
    if project_type == 'web':
        create_web_project(project_dir, name, framework)
    elif project_type == 'python':
        create_python_project(project_dir, name)
    
    click.echo(f"✅ Extension '{name}' created successfully!")
    click.echo(f"📁 Project location: {project_dir.absolute()}")
    click.echo(f"🚀 Next steps:")
    click.echo(f"   cd {name}")
    click.echo(f"   pet run")


def create_web_project(project_dir, name, framework):
    """Create a web-based extension project."""
    # Create basic structure
    (project_dir / 'app').mkdir()
    (project_dir / 'assets').mkdir()
    (project_dir / 'assets' / 'css').mkdir()
    (project_dir / 'assets' / 'js').mkdir()
    
    # Create manifest.json
    manifest = {
        "name": name,
        "version": "1.0.0",
        "description": f"{name} extension",
        "type": "web",
        "entry_point": "app/index.html",
        "permissions": [],
        "icon": "assets/icon.png"
    }
    
    with open(project_dir / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Create HTML file
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
    <div id="app">
        <h1>Welcome to {name}</h1>
        <p>Your extension is ready to go!</p>
        <button id="actionBtn">Click me!</button>
    </div>
    <script src="../assets/js/main.js"></script>
</body>
</html>"""
    
    with open(project_dir / 'app' / 'index.html', 'w') as f:
        f.write(html_content)
    
    # Create CSS file
    css_content = """body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

#app {
    max-width: 600px;
    margin: 0 auto;
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

h1 {
    color: #333;
    text-align: center;
}

button {
    background-color: #007cba;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
}

button:hover {
    background-color: #005a87;
}"""
    
    with open(project_dir / 'assets' / 'css' / 'style.css', 'w') as f:
        f.write(css_content)
    
    # Create JS file
    js_content = """document.addEventListener('DOMContentLoaded', function() {
    const actionBtn = document.getElementById('actionBtn');
    
    actionBtn.addEventListener('click', function() {
        alert('Hello from your extension!');
    });
    
    console.log('Extension loaded successfully');
});"""
    
    with open(project_dir / 'assets' / 'js' / 'main.js', 'w') as f:
        f.write(js_content)


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