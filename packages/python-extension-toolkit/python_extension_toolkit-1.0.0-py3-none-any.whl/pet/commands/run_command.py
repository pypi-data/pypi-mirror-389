"""Run command for starting the development server."""

import click
import os
import json
import subprocess
import sys
from pathlib import Path
from flask import Flask, send_from_directory, render_template_string
from flask_cors import CORS
import threading
import time
import webbrowser


@click.command()
@click.option('--port', help='Port to run the development server on')
@click.option('--host', help='Host to bind the server to')
@click.option('--open-browser/--no-browser', default=None, help='Open browser automatically')
def run(port, host, open_browser):
    """Start the development server for the extension."""
    
    # Check if we're in an extension project
    if not Path('manifest.json').exists():
        click.echo("❌ No manifest.json found. Make sure you're in an extension project directory.", err=True)
        click.echo("💡 Use 'pet init' to create a new extension project.")
        return
    
    # Interactive configuration if not provided
    if not port:
        port = click.prompt('🌐 Server port', default=5000, type=int)
    
    if not host:
        host = click.prompt('🖥️ Server host', default='127.0.0.1')
    
    if open_browser is None:
        open_browser = click.confirm('🌍 Open browser automatically?', default=True)
    
    # Load manifest
    try:
        with open('manifest.json', 'r') as f:
            manifest = json.load(f)
    except Exception as e:
        click.echo(f"❌ Error reading manifest.json: {e}", err=True)
        return
    
    extension_type = manifest.get('type', 'web')
    entry_point = manifest.get('entry_point', 'app/index.html')
    
    click.echo(f"🚀 Starting development server for '{manifest['name']}'...")
    click.echo(f"📋 Type: {extension_type}")
    click.echo(f"🌐 Server: http://{host}:{port}")
    
    if extension_type == 'python':
        run_python_extension(entry_point, port, host, open_browser)
    else:
        run_web_extension(entry_point, port, host, open_browser, manifest)


def run_python_extension(entry_point, port, host, open_browser):
    """Run a Python-based extension."""
    if not Path(entry_point).exists():
        click.echo(f"❌ Entry point file not found: {entry_point}", err=True)
        return
    
    # Install requirements if requirements.txt exists
    if Path('requirements.txt').exists():
        click.echo("📦 Installing requirements...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      capture_output=True)
    
    # Set environment variables
    env = os.environ.copy()
    env['FLASK_APP'] = entry_point
    env['FLASK_ENV'] = 'development'
    env['FLASK_RUN_PORT'] = str(port)
    env['FLASK_RUN_HOST'] = host
    
    if open_browser:
        # Open browser after a short delay
        def open_browser_delayed():
            time.sleep(2)
            webbrowser.open(f'http://{host}:{port}')
        
        threading.Thread(target=open_browser_delayed, daemon=True).start()
    
    click.echo("🔧 Starting Python Flask server...")
    
    # Run the Python application
    try:
        subprocess.run([sys.executable, entry_point], env=env, cwd=os.getcwd())
    except KeyboardInterrupt:
        click.echo("\\n🛑 Development server stopped.")


def run_web_extension(entry_point, port, host, open_browser, manifest):
    """Run a web-based extension with a simple file server."""
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/')
    def index():
        """Serve the main entry point."""
        try:
            if Path(entry_point).exists():
                return send_from_directory('.', entry_point)
            else:
                return render_template_string(get_default_page(manifest)), 404
        except Exception as e:
            return f"Error serving file: {e}", 500
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        """Serve static files."""
        try:
            return send_from_directory('.', filename)
        except Exception as e:
            return f"File not found: {filename}", 404
    
    @app.route('/api/manifest')
    def get_manifest():
        """Serve the manifest.json for development tools."""
        return manifest
    
    if open_browser:
        # Open browser after a short delay
        def open_browser_delayed():
            time.sleep(1)
            webbrowser.open(f'http://{host}:{port}')
        
        threading.Thread(target=open_browser_delayed, daemon=True).start()
    
    click.echo("🔧 Starting development server...")
    
    try:
        app.run(host=host, port=port, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        click.echo("\\n🛑 Development server stopped.")


def get_default_page(manifest):
    """Return a default page when entry point is not found."""
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{manifest.get("name", "Extension")} - Development</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .error {{ color: #d32f2f; }}
        .info {{ color: #1976d2; }}
        code {{ 
            background: #f5f5f5; 
            padding: 2px 6px; 
            border-radius: 3px; 
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 {manifest.get("name", "Extension")} Development Server</h1>
        <p class="error">⚠️ Entry point file not found: <code>{manifest.get("entry_point", "app/index.html")}</code></p>
        <p class="info">The development server is running, but your entry point file is missing.</p>
        <hr>
        <h3>Extension Info:</h3>
        <p><strong>Name:</strong> {manifest.get("name", "N/A")}</p>
        <p><strong>Version:</strong> {manifest.get("version", "N/A")}</p>
        <p><strong>Type:</strong> {manifest.get("type", "web")}</p>
        <p><strong>Description:</strong> {manifest.get("description", "N/A")}</p>
    </div>
</body>
</html>
    '''