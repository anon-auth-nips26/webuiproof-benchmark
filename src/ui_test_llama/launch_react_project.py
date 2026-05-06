import os
import http.server
import socketserver
import webbrowser
from pathlib import Path

# Configuration
PROJECT_DIR = Path("./data/uigen/run_2025-06-13T20:03:34.669266_e67a84")
PORT = 3000  # Common port for React apps
HOST = "0.0.0.0"

def launch_react_project():
    # Verify the project directory exists
    if not PROJECT_DIR.exists():
        print(f"Error: Project directory not found at {PROJECT_DIR}")
        return

    # Check for required files
    required_files = ['index.html']
    for file in required_files:
        if not (PROJECT_DIR / file).exists():
            print(f"Error: Required file '{file}' not found in project directory")
            return

    # Change to the project directory
    os.chdir(PROJECT_DIR)
    
    # Create and start the server
    handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer((HOST, PORT), handler) as httpd:
        url = f"http://{HOST}:{PORT}"
        print(f"Serving React project at {url}")
        print("Press Ctrl+C to stop the server")
        
        # Try to open the browser automatically
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Could not open browser: {e}")
        
        # Start the server
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
        except Exception as e:
            print(f"Server error: {e}")

if __name__ == "__main__":
    # Change to the script's directory first
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Launch the React project
    launch_react_project()
