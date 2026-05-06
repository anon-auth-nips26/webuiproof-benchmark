import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import posixpath
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import browser_cookie3
import requests
from requests.exceptions import RequestException
from tqdm import tqdm
# Import start_services directly when running as a script
try:
    from start_service import start_services
except ImportError:
    # When running as a module
    try:
        from src.ui_test_llama.start_service import start_services
    except ImportError:
        print("Warning: Could not import start_services")
        start_services = None
import http.server
import socketserver
import importlib.util
import sys
import webbrowser
import socket


# Custom HTTP request handler with better error handling
class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def copyfile(self, source, outputfile):
        """Copy all data between two file objects.
        Handles BrokenPipeError when client disconnects prematurely.
        """
        try:
            # Use smaller buffer size to avoid large memory usage
            buffer_size = 64 * 1024  # 64KB buffer instead of default
            shutil.copyfileobj(source, outputfile, buffer_size)
        except (BrokenPipeError, ConnectionResetError) as e:
            # Client disconnected before response was fully sent
            self.log_error(f"{type(e).__name__}: Client disconnected prematurely")
            return
        except socket.timeout:
            self.log_error("Socket timeout during file transfer")
            return
        except Exception as e:
            self.log_error(f"Error during file transfer: {type(e).__name__}: {str(e)}")
            return
    
    # Class variable to store project directories for each server instance
    project_directories = {}
    
    @classmethod
    def set_project_directory(cls, directory, port):
        cls.project_directories[port] = directory
        print(f"Set project directory for handler on port {port}: {directory}")
    
    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.
        
        Override to ensure we're always serving from the correct project directory.
        """
        # Get the server port to identify which project directory to use
        server_port = self.server.server_address[1]
        project_dir = self.project_directories.get(server_port)
        
        if project_dir:
            # Remove query parameters if present
            path = path.split('?', 1)[0]
            path = path.split('#', 1)[0]
            # Normalize path
            path = posixpath.normpath(urllib.parse.unquote(path))
            words = path.split('/')
            words = filter(None, words)
            # Start from the project directory instead of current directory
            path = project_dir
            for word in words:
                if os.path.dirname(word) or word in (os.curdir, os.pardir):
                    # Ignore components that might navigate outside the directory
                    continue
                path = os.path.join(path, word)
            return path
        else:
            return super().translate_path(path)
    
    def do_HEAD(self):
        """Serve a HEAD request.
        
        This method properly handles HEAD requests by determining the correct content type
        and setting appropriate headers, just like in GET but without sending the body.
        """
        self.log_message(f"HEAD request for path: {self.path}")
        
        # Translate the path to a file path
        file_path = self.translate_path(self.path)
        self.log_message(f"HEAD translated to file path: {file_path}")
        
        # Check if the file exists
        if os.path.isfile(file_path):
            self.log_message(f"File exists for HEAD: {file_path}")
            # Determine content type based on file extension
            _, ext = os.path.splitext(file_path)
            content_type = self.extensions_map.get(ext, 'application/octet-stream')
            
            # Get file size for Content-Length header
            try:
                fs = os.fstat(os.open(file_path, os.O_RDONLY))
                file_size = fs[6]
            except Exception as e:
                self.log_error(f"Error getting file size: {e}")
                file_size = 0
                
            # Send appropriate headers
            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.send_header("Content-Length", str(file_size))
            self.end_headers()
        else:
            # Handle non-existent files or directory requests
            self.log_message(f"File does not exist for HEAD: {file_path}")
            
            # For client-side routing in SPA, handle like we would in do_GET
            if self.path.endswith('/') or not self.path:
                index_path = os.path.join(file_path, 'index.html')
                if os.path.isfile(index_path):
                    self.log_message(f"Serving index.html for HEAD: {index_path}")
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    return
            elif not os.path.isfile(file_path) and '.' not in os.path.basename(self.path):
                self.log_message(f"Path appears to be a route, serving index.html for HEAD")
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                return
                
            # If we get here, the file doesn't exist
            self.send_error(404, "File not found")
    
    def do_GET(self):
        """Serve a GET request with enhanced debugging."""
        self.log_message(f"GET request for path: {self.path}")
        
        # Special handling for Next.js static files
        if '/_next/' in self.path:
            self.log_message(f"Handling Next.js static file: {self.path}")
        
        # Check if the file exists in our directory
        file_path = self.translate_path(self.path)
        self.log_message(f"Translated to file path: {file_path}")
        
        if os.path.isfile(file_path):
            self.log_message(f"File exists: {file_path}")
        else:
            self.log_message(f"File does not exist: {file_path}")
            
            # If path ends with / or is empty, try to serve index.html
            if self.path.endswith('/') or not self.path:
                index_path = os.path.join(file_path, 'index.html')
                if os.path.isfile(index_path):
                    self.log_message(f"Serving index.html instead: {index_path}")
                    self.path = '/index.html'
                    return self.do_GET()
            # For client-side routing in SPA, serve index.html for non-file paths
            elif not os.path.isfile(file_path) and '.' not in os.path.basename(self.path):
                self.log_message(f"Path appears to be a route, serving index.html")
                self.path = '/index.html'
                return self.do_GET()
        
        # Call the parent method to actually serve the file
        return super().do_GET()
    
    def handle(self):
        """Handle multiple requests if necessary.
        Override to add better error handling.
        """
        try:
            # Set a reasonable timeout for socket operations
            self.connection.settimeout(30)  # 30 seconds timeout
            super().handle()
        except (ConnectionResetError, BrokenPipeError) as e:
            self.log_error(f"{type(e).__name__}: Connection error during request handling")
        except socket.timeout:
            self.log_error("Socket timeout during request handling")
        except Exception as e:
            self.log_error(f"Error during request handling: {type(e).__name__}: {str(e)}")
    
    def log_message(self, format, *args):
        """Log an arbitrary message.
        Override to provide more detailed logging.
        """
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))


def load_json(in_file):
    with open(in_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_json(data, out_file):
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_jsonl(in_file):
    datas = []
    with open(in_file, "r", encoding="utf-8") as f:
        for line in tqdm(f):
            datas.append(json.loads(line))
    return datas


def kill_process_on_port(port):
    """Kill any process that is using the specified port."""
    try:
        # Find process using the port
        print(f"Checking for processes using port {port}...")
        if sys.platform.startswith('win'):
            # Windows
            result = subprocess.run(
                f"netstat -ano | findstr :{port}", 
                shell=True, 
                text=True, 
                capture_output=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if f":{port}" in line:
                        parts = line.strip().split()
                        if len(parts) > 4:
                            pid = parts[-1]
                            print(f"Found process {pid} using port {port}, killing it...")
                            try:
                                subprocess.run(f"taskkill /F /PID {pid}", shell=True)
                                print(f"Process {pid} killed")
                            except Exception as e:
                                print(f"Error killing process {pid}: {e}")
        else:
            # Linux/Mac
            result = subprocess.run(
                f"lsof -i :{port} | grep LISTEN", 
                shell=True, 
                text=True, 
                capture_output=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) > 1:
                        pid = parts[1]
                        print(f"Found process {pid} using port {port}, killing it...")
                        try:
                            os.kill(int(pid), signal.SIGKILL)
                            print(f"Process {pid} killed")
                        except Exception as e:
                            print(f"Error killing process {pid}: {e}")
        
        # Verify port is free
        time.sleep(1)  # Give OS time to free the port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        if result == 0:
            print(f"Warning: Port {port} is still in use after kill attempt")
        else:
            print(f"Port {port} is now free")
            
    except Exception as e:
        print(f"Error checking/killing process on port {port}: {e}")


def save_jsonl(datas, out_file, mode="w"):
    with open(out_file, mode, encoding="utf-8") as f:
        for data in tqdm(datas):
            f.write(json.dumps(data, ensure_ascii=False) + "\n")



ui_prompt_template = """
    Task: {task}
    Preconditions: {preconditions}
    Procedure: {procedure}
    Expected Result: {expected_result}

    Instructions:
    - First, ensure the preconditions are met before attempting the task.
    - Attempt the task as a user would, using the UI elements available. You should follow the Procedure given in the task.
    - Make multiple attempts if needed to try and achieve the expected result.
    - Observe whether the expected result is fully, partially, or not at all achieved.
    - IMPORTANT: You can at most interact with the website 15 times. If the limit is reached, directly output your answer.

    At the end of your testing, answer only with one of the following:
    - YES: if the expected result was fully achieved.
    - NO: if the expected result could not be achieved at all.
    - PARTIAL: if only some aspects of the expected result were achieved.
"""


def run_server(httpd):
    """Run the HTTP server in a separate thread with improved error handling"""
    try:
        print(f"Starting HTTP server on {httpd.server_address}")
        # Set a shorter timeout to make the server more responsive
        httpd.timeout = 0.5
        # Print a message to confirm server is ready
        print(f"Server is ready at http://{httpd.server_address[0]}:{httpd.server_address[1]}/")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped by keyboard interrupt")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"Port {httpd.server_address[1]} is already in use")
            kill_process_on_port(httpd.server_address[1])
        else:
            print(f"Server error (OSError): {e}")
    except Exception as e:
        print(f"Server error: {type(e).__name__}: {e}")
    finally:
        print(f"Shutting down server on {httpd.server_address}")
        httpd.server_close()


def launch_react_project(project_dir, preferred_port=None):
    # Try ports in this range
    start_port = 3001
    end_port = 3020  # Try up to port 3020
    
    # Use preferred port if specified
    if preferred_port is not None:
        print(f"Using preferred port: {preferred_port}")
        # Try the preferred port first, then fall back to the range if it fails
        port_list = [preferred_port] + list(range(start_port, end_port + 1))
    else:
        port_list = range(start_port, end_port + 1)
    HOST = "localhost"  # Use localhost instead of 0.0.0.0 for better compatibility
    httpd = None

    # Ensure project_dir is an absolute path
    project_dir = os.path.abspath(project_dir)
    print(f"Using absolute project directory: {project_dir}")
    
    # Check for required files
    required_files = ['index.html']
    for file in required_files:
        if not os.path.exists(os.path.join(project_dir, file)):
            print(f"Error: Required file '{file}' not found in project directory: {project_dir}")
            return None, None, None

    # Change to the project directory
    original_dir = os.getcwd()
    print(f"Current original directory: {original_dir}")
    os.chdir(project_dir)
    print(f"Changed to project directory: {project_dir}")
    
    # We'll set the project directory in the handler class after we know the port
    
    # Create and start the server
    handler = CustomHTTPRequestHandler
    
    # Allow socket reuse to avoid "address already in use" errors
    socketserver.TCPServer.allow_reuse_address = True
    
    # Try different ports until one works
    for PORT in port_list:
        try:
            httpd = socketserver.TCPServer((HOST, PORT), handler)
            # Set a timeout to allow for keyboard interrupts
            httpd.timeout = 1
            
            # Set the project directory in the handler class with the port
            CustomHTTPRequestHandler.set_project_directory(project_dir, PORT)
            print(f"Set project directory in handler for port {PORT}: {project_dir}")
            
            # Start the server in a separate thread
            server_thread = threading.Thread(target=run_server, args=(httpd,))
            server_thread.daemon = True  # This ensures the thread will exit when the main program exits
            server_thread.start()
            
            url = f"http://{HOST}:{PORT}"
            print(f"Serving React project at {url} (port {PORT})")
            
            # Wait for the server to be ready before proceeding
            server_ready = False
            max_wait_time = 60  # Increase to 60 seconds
            start_time = time.time()
            print(f"Waiting for server to be ready on port {PORT}...")
            
            # Check server readiness with increasing backoff
            retry_count = 0
            max_retries = 10  # Increase max retries
            while time.time() - start_time < max_wait_time and not server_ready and retry_count < max_retries:
                try:
                    # Try a simple socket connection first (most reliable)
                    print(f"Attempting socket connection to {HOST}:{PORT} (attempt {retry_count + 1}/{max_retries})")
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)  # Increase socket timeout to 5 seconds
                    result = sock.connect_ex((HOST, PORT))
                    sock.close()
                    
                    if result == 0:
                        print(f"Socket connection successful on port {PORT}")
                        # Now try a GET request to verify HTTP server is working
                        try:
                            # Use a session with keep-alive disabled
                            print(f"Sending GET request to {url}")
                            session = requests.Session()
                            session.headers['Connection'] = 'close'
                            response = session.get(url, timeout=10)  # Increase HTTP timeout to 10 seconds
                            print(f"HTTP GET request successful with status {response.status_code}")
                            server_ready = True
                            # Add a small delay to ensure server is fully ready
                            time.sleep(2)
                        except Exception as http_err:
                            print(f"Socket connected but HTTP request failed: {str(http_err)}")
                            retry_count += 1
                            time.sleep(2)  # Increase delay before retry
                    else:
                        print(f"Socket connection failed with error code {result}, waiting...")
                        retry_count += 1
                        time.sleep(min(2.0 * retry_count, 5))  # Longer backoff
                except Exception as e:
                    print(f"Server connection check failed: {str(e)}")
                    retry_count += 1
                    time.sleep(min(1.0 * retry_count, 3))  # Shorter backoff
            
            # Try to open the browser automatically
            if server_ready:
                try:
                    browser = webbrowser.get()
                    browser.open(url)
                    print(f"Opened browser to {url}")
                except Exception as e:
                    print(f"Could not open browser: {e}")
            else:
                print(f"Warning: Server may not be fully ready on port {PORT}")
            
            # Return the server object, port, and thread
            # Restore original directory before returning
            os.chdir(original_dir)
            return httpd, PORT, server_thread
            
        except OSError as e:
            if e.errno == 98:  # Address already in use
                print(f"Port {PORT} is already in use, trying next port...")
                if httpd:
                    httpd.server_close()
                continue
            else:
                print(f"Failed to start server: {e}")
                if httpd:
                    httpd.server_close()
                os.chdir(original_dir)
                return None, None, None
        except Exception as e:
            print(f"Failed to start server: {e}")
            if httpd:
                httpd.server_close()
            os.chdir(original_dir)
            return None, None, None
    
    # If we've tried all ports and none worked
    print(f"Failed to find an available port between {start_port} and {end_port}")
    os.chdir(original_dir)
    return None, None, None


def create_tasks_test(test_file, ports, tasks_file, manifold_id):
    print('Create tasks test...')
    datas = load_jsonl(test_file)
    tasks = []
    for idx, data in tqdm(enumerate(datas)):
        app = f"{idx + 1:06d}-{manifold_id}"  
        print('app', app, 'port', ports)
        # Skip if app not in ports or if port is not a valid number
        if app not in ports or not isinstance(ports[app], int):
            print(f"Skipping {app} due to invalid or missing port")
            continue
            
        for ui_idx, ui_instruct in enumerate(data["ui_instruct"]):
            instruction = ui_prompt_template.format(
                task=ui_instruct["task"],
                procedure="",
                expected_result=ui_instruct["expected_result"]
            )
            # Ensure URL ends with trailing slash for consistency
            url = f"http://localhost:{ports[app]}/"
            tasks.append({
                "web_name": data["id"],
                "id": f"{app}_{ui_idx}",
                "ques": instruction,
                "web": url,  # Ensure consistent URL format
                "port": ports[app],  # Add port directly to task
                "expected_result": ui_instruct["expected_result"],
                "task": ui_instruct["task"]
            })
    
    if not tasks:
        print("Warning: No valid tasks were created. Check if ports were detected correctly.")
    else:
        print(f"Created {len(tasks)} valid tasks")
        
    save_jsonl(tasks, tasks_file)


def create_tasks_test_formatted(test_response_file, ports, tasks_file, manifold_id):
    """
    Creates test tasks from formatted test response files in the filtered_webgen_formatted directory.
    
    Args:
        test_response_file (str): Path to the test response JSON file
        ports (dict): Dictionary mapping app IDs to port numbers
        tasks_file (str): Path to save the generated tasks
        manifold_id (str): Manifold ID to use in app IDs
    """
    print(f'Creating tasks test from formatted response file: {test_response_file}')
    
    try:
        # Load the test response file
        with open(test_response_file, 'r') as f:
            data = json.load(f)

        print("data: ", data)
        
        # Extract the test ID from the filename
        # Format: test_response_000016-2.json -> 000016-2
        test_id = os.path.basename(test_response_file).split(".")[0]
        
        
        tasks = []
        app = test_id + '-' + str(manifold_id) # Use the test ID directly as the app ID
        
        # Check if this app has a port assigned
        if app not in ports or not isinstance(ports[app], int):
            print(f"Skipping {app} due to invalid or missing port")
            return
        test_cases_num = len(data['test_cases']['functionality_testing']) + len(data['test_cases']['data_display_testing']) + len(data['test_cases']['design_validation_testing'])
        print(f"Found {test_cases_num} test cases for {app}")
        ports = {}
        for i in range(test_cases_num): ports[i] = 8000+i
        
        test_case_idx = 0
        # Process each test case in the response file
        if 'test_cases' in data:
            # Process functionality testing cases
            if 'functionality_testing' in data['test_cases']:
                for tc_idx, test_case in enumerate(data['test_cases']['functionality_testing']):
                    # Create instruction from test case data
                    procedure = "\n".join(test_case.get('procedure', []))
                    task_description = test_case.get('name', '') + ": " + test_case.get('objective', '')
                    preconditions = test_case.get('preconditions', 'None specified')
                    instruction = ui_prompt_template.format(
                        task=task_description,
                        procedure=procedure,
                        preconditions=preconditions,
                        expected_result=test_case.get('expected_results', '')
                    )
                    
                    # Ensure URL ends with trailing slash for consistency
                    url = f"http://localhost:{ports[test_case_idx]}/"
                    test_case_id = test_case.get('id')
                    # Create task entry
                    tasks.append({
                        "web_name": f"test_{app}",
                        "id": f"{app}_FT_{test_case_id}",
                        "ques": instruction,
                        "web": url,
                        "port": ports[test_case_idx],
                        "expected_result": test_case.get('expected_results', ''),
                        "task": task_description
                    })
                    test_case_idx += 1            
            # Process data display testing cases
            if 'data_display_testing' in data['test_cases']:
                for tc_idx, test_case in enumerate(data['test_cases']['data_display_testing']):
                    # Create instruction from test case data
                    procedure = "\n".join(test_case.get('procedure', []))
                    task_description = test_case.get('name', '') + ": " + test_case.get('objective', '')
                    preconditions = test_case.get('preconditions', 'None specified')
                    instruction = ui_prompt_template.format(
                        task=task_description,
                        procedure=procedure,
                        preconditions=preconditions,
                        expected_result=test_case.get('expected_results', '')
                    )
                    
                    # Ensure URL ends with trailing slash for consistency
                    url = f"http://localhost:{ports[test_case_idx]}/"
                    test_case_id = test_case.get('id')
                    # Create task entry
                    tasks.append({
                        "web_name": f"test_{app}",
                        "id": f"{app}_DDT_{test_case_id}",
                        "ques": instruction,
                        "web": url,
                        "port": ports[test_case_idx],
                        "expected_result": test_case.get('expected_results', ''),
                        "task": task_description
                    })
                    test_case_idx += 1   
            # Process data display testing cases
            if 'design_validation_testing' in data['test_cases']:
                for tc_idx, test_case in enumerate(data['test_cases']['design_validation_testing']):
                    # Create instruction from test case data
                    procedure = "\n".join(test_case.get('procedure', []))
                    task_description = test_case.get('name', '') + ": " + test_case.get('objective', '')
                    preconditions = test_case.get('preconditions', 'None specified')
                    instruction = ui_prompt_template.format(
                        task=task_description,
                        procedure=procedure,
                        preconditions=preconditions,
                        expected_result=test_case.get('expected_results', '')
                    )
                    
                    # Ensure URL ends with trailing slash for consistency
                    url = f"http://localhost:{ports[test_case_idx]}/"
                    test_case_id = test_case.get('id')
                    # Create task entry
                    tasks.append({
                        "web_name": f"test_{app}",
                        "id": f"{app}_DVT_{test_case_id}",
                        "ques": instruction,
                        "web": url,
                        "port": ports[test_case_idx],
                        "expected_result": test_case.get('expected_results', ''),
                        "task": task_description
                    })
                    test_case_idx += 1   
        
        if not tasks:
            print("Warning: No valid tasks were created. Check if the test response file contains valid test cases.")
        else:
            print(f"Created {len(tasks)} valid tasks")
            
        # Save the tasks to the output file
        save_jsonl(tasks, tasks_file)
        
    except json.JSONDecodeError as e:
        # Handle JSON parsing errors, using the robust parsing approach from memory
        print(f"Error parsing JSON in {test_response_file}: {e}")
        try:
            # Try to find the first occurrence of '{' to identify the start of the JSON object
            with open(test_response_file, 'r') as f:
                content = f.read()
            
            # Find the first occurrence of '{'
            start_idx = content.find('{')
            if start_idx >= 0:
                # Extract just the JSON part
                json_content = content[start_idx:]
                # Parse the JSON
                data = json.loads(json_content)
                print(f"Successfully parsed JSON after removing prefix")
                # Continue processing...
            else:
                print(f"Could not find valid JSON start in {test_response_file}")
        except Exception as e2:
            print(f"Failed to recover from JSON parsing error: {e2}")
    except Exception as e:
        print(f"Error processing {test_response_file}: {e}")


def process_all_formatted_test_responses(filtered_dir, output_dir, case_id , manifold_id):
    """
    Process all test response files in the filtered_webgen_formatted directory and create task files.
    
    Args:
        filtered_dir (str): Directory containing the filtered test response files
        output_dir (str): Directory to save the generated task files
        manifold_id (str): Manifold ID to use in app IDs
    """
    print(f"Processing all formatted test responses in {filtered_dir}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all test response files
    test_response_files = []
    for file in os.listdir(filtered_dir):
        if file.endswith('.json'):
            test_response_files.append(os.path.join(filtered_dir, file))
    
    print(f"Found {len(test_response_files)} test response files")
    
    # Assign ports to each test ID
    ports = {}
    start_port = 3000
    for file in test_response_files:
        test_id = os.path.basename(file).split(".")[0] 
        if test_id == case_id:
            ports[test_id + '-' + str(manifold_id)] = start_port
        start_port += 1

    # Process each test response file
    for file in tqdm(test_response_files):
        test_id = os.path.basename(file).split(".")[0]
        print('here..... ', test_id, " | ", case_id)
        if test_id == case_id:
            tasks_file = os.path.join(output_dir, f"test_tasks_{test_id}-{manifold_id}.jsonl")
            # print('crearte file.....', file)
            create_tasks_test_formatted(file, ports, tasks_file, manifold_id)
    
    print(f"Processed {len(test_response_files)} test response files")
    print(f"Task files saved to {output_dir}")
    
    return ports

    

def run_webvoyager(input_dir, port_file_path=None, task_file_path=None, data_src='llama4', formatted_output_folder='webgen_formatted'):
    import re
    
    input_dir = Path(input_dir)  # Path object for convenience
    if port_file_path is None:
        ports_file = Path(f"{base_dir}/results_{formatted_output_folder}/ports.json")
    else:
        ports_file = Path(port_file_path)
    
    if task_file_path is None:
        tasks_file = Path(f"{base_dir}/results_{formatted_output_folder}/tasks_test_with_answer.jsonl")
    else:
        tasks_file = Path(task_file_path)
    
    # Check if the necessary files exist
    if not ports_file.exists():
        print(f"Error: Ports file not found at {ports_file}")
        return
    if not tasks_file.exists():
        print(f"Error: Tasks file not found at {tasks_file}")
        return
    
    # Load ports to verify React servers are running
    try:
        with open(ports_file, 'r') as f:
            ports = json.load(f)
        
        # Load tasks
        if task_file_path.endswith('.jsonl'):
            tasks = load_jsonl(task_file_path)
            print('len of tasks: ', len(tasks))
            num_of_tasks = len(tasks)
        else:
            # For regular JSON files
            with open(tasks_file, 'r') as f:
                tasks = json.load(f)
        updated_tasks = False
        
        # Check for each app ID in ports
        for app_id, port in ports.items():
            base_url = f"http://localhost:{port}/"
            print(f"Checking if React server for {app_id} is running at {base_url}")
            
            # Check if port is in use and if the server is responding to HTTP requests
            server_running = False
            max_attempts = 5
            
            # Try multiple times with increasing timeout
            for attempt in range(1, max_attempts + 1):
                print(f"Checking for React app at {base_url} (attempt {attempt}/{max_attempts})")
                
                try:
                    # First check if the port is open with a socket connection
                    print(f"Trying socket connection to localhost:{port}")
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(10)  # Increase timeout to 10 seconds
                    result = sock.connect_ex(('localhost', port))
                    sock.close()
                    
                    if result == 0:
                        print(f"Socket connection successful on port {port}")
                        # Now try an HTTP GET request to verify the server is working
                        try:
                            print(f"Sending GET request to {base_url}")
                            # Use a session with keep-alive disabled
                            session = requests.Session()
                            session.headers['Connection'] = 'close'
                            response = session.get(base_url, timeout=15)  # Increased timeout
                            
                            print(f"GET request successful with status code {response.status_code}")
                            server_running = True
                            break
                        except requests.exceptions.RequestException as e:
                            print(f"GET request failed: {e}")
                            # If socket worked but HTTP failed, the server might still be starting up
                            time.sleep(3)
                    else:
                        print(f"Socket connection failed with error code {result}, waiting...")
                        time.sleep(min(2.0 * attempt, 5))  # Longer backoff with each attempt
                except Exception as e:
                    print(f"Error checking server: {str(e)}")
                    time.sleep(2)  # Wait before retrying
            
            if not server_running:
                # Look for the React app directory in the data/uigen/llama4_data folder
                # First, check if we have the app ID in the llama_url_mappings.json file
                try:
                    if data_src == 'llama4':
                        with open('./data/parsed_llama4_webgen_30.json', 'r') as f:
                            mappings = json.load(f)
                    elif data_src == 'claude4':
                        with open('./data/parsed_claude4_webgen_30.json', 'r') as f:
                            mappings = json.load(f)
                    elif data_src == 'gemini25':
                        with open('./data/parsed_gemini25_webgen_30.json', 'r') as f:
                            mappings = json.load(f)
                    elif data_src == 'gpt41':
                        with open('./data/parsed_gpt41_webgen_30.json', 'r') as f:
                            mappings = json.load(f)
                    
                    # Find the mapping for this app_id
                    app_mapping = None
                    for mapping in mappings:
                        if mapping['test_id'] == app_id:
                            app_mapping = mapping
                            break
                    
                    if app_mapping and app_mapping['manifold_dir']:
                        # Extract the directory name from the manifold URL
                        for manifold_url in app_mapping['manifold_dir']:
                            dir_name = manifold_url.split('/')[-1]
                            app_dir = Path(f'./data/uigen/{data_src}/{dir_name}')
                            
                            # Check if the directory exists
                            if app_dir.exists():
                                print(f"Found potential React app directory at {app_dir}")
                                
                                # List files in the directory to find the main HTML file
                                html_files = []
                                for file in app_dir.glob('*.html'):
                                    html_files.append(file.name)
                                
                                if html_files:
                                    print(f"Found HTML files: {html_files}")
                                    # Prefer index.html if it exists
                                    main_html = 'index.html' if 'index.html' in html_files else html_files[0]
                                    print(f"Using {main_html} as the main HTML file")
                                    
                                    # Determine the correct directory to serve
                                    extract_dir = os.path.join('results/extract', app_id)
                                    if os.path.exists(extract_dir):
                                        print(f"Using extract directory for HTTP server: {extract_dir}")
                                        serve_dir = extract_dir
                                    else:
                                        print(f"Extract directory not found, using app directory: {app_dir}")
                                        serve_dir = app_dir
                                    
                                    # Start a simple HTTP server to serve the React app
                                    class HttpRequestHandler(CustomHTTPRequestHandler):
                                        def __init__(self, *args, **kwargs):
                                            print(f"HTTP server serving from directory: {serve_dir}")
                                            super().__init__(*args, directory=str(serve_dir), **kwargs)
                                    
                                    # Start the server
                                    def run_server():
                                        try:
                                            # Bind to all interfaces (0.0.0.0) instead of just localhost
                                            # This ensures the server is accessible from all network interfaces
                                            with socketserver.TCPServer(("0.0.0.0", port), HttpRequestHandler) as httpd:
                                                print(f"Serving React app at http://localhost:{port}/ and http://0.0.0.0:{port}/")
                                                # Allow socket reuse to avoid "address already in use" errors
                                                httpd.allow_reuse_address = True
                                                # Set a timeout to make the server more responsive
                                                httpd.timeout = 0.5
                                                httpd.serve_forever()
                                        except Exception as e:
                                            print(f"Error in HTTP server thread: {str(e)}")
                                    
                                    server_thread = threading.Thread(target=run_server, daemon=True)
                                    server_thread.start()
                                    print(f"Started HTTP server thread for {app_id}")
                                    
                                    # Wait for server to be ready
                                    server_ready = False
                                    max_retries = 6  # 6 retries × 2 seconds = 12 seconds max
                                    for retry in range(max_retries):
                                        print(f"Waiting for HTTP server to be ready (attempt {retry+1}/{max_retries})...")
                                        time.sleep(2)  # Wait 2 seconds between checks
                                        
                                        # Try to access the main HTML file
                                        test_url = f"{base_url}{main_html}"
                                        print(f"Testing URL: {test_url}")
                except Exception as e:
                    print(f"Error starting HTTP server for {app_id}: {str(e)}")
            else: 
                server_ready = False
                working_url = None
                    
                # Verify that we're using the correct directory for the HTTP server
                extract_dir = os.path.join(f'/local/rcs/yunyun/WebUI-AutoEvaluation/results_{formatted_data_src}/extract/{data_src}', app_id, 'out')
                print(f"Checking if extract directory exists: {extract_dir}")
                if os.path.exists(extract_dir):
                    print(f"Extract directory exists, listing contents:")
                    for item in os.listdir(extract_dir):
                        print(f"  - {item}")
                else:
                    print(f"Warning: Extract directory does not exist: {extract_dir}")
                
                # Try different possible URLs for the React app
                possible_paths = [
                    "",  # Root path
                    "index.html",
                    "modelOutputPage.html",
                    "404.html"
                ]
                
                # Give the server more time to start up before checking
                print(f"Waiting 5 seconds for server to start up fully...")
                time.sleep(5)
                
                # Try each path with multiple attempts
                for path in possible_paths:
                    max_retries = 5  # Increased retries
                    for attempt in range(max_retries):
                        try:
                            test_url = f"{base_url}{path}"
                            print(f"Checking for React app at {test_url} (attempt {attempt+1}/{max_retries})")
                            
                            # Use a session with keep-alive disabled to avoid connection pooling issues
                            session = requests.Session()
                            session.headers['Connection'] = 'close'  # Disable keep-alive
                            
                            # Use a HEAD request first to check if server is responding (faster)
                            print(f"Sending HEAD request to {test_url}")
                            head_response = session.head(
                                test_url, 
                                timeout=5  # Short timeout for HEAD
                            )
                            
                            if head_response.status_code == 200:
                                print(f"Server responded to HEAD request with status 200")
                                
                                # Now try a GET request with longer timeout
                                print(f"Sending GET request to {test_url}")
                                response = session.get(
                                    test_url, 
                                    timeout=30,  # Longer timeout for GET
                                    stream=True  # Stream the response to avoid reading the entire content
                                )
                                
                                # Just check the headers and status code, don't read the full response
                                if response.status_code == 200:
                                    content_type = response.headers.get('content-type', '')
                                    if 'text/html' in content_type:
                                        # Close the response without reading the body
                                        response.close()
                                        print(f"Found HTML content at {test_url}")
                                        server_ready = True
                                        working_url = test_url
                                        break
                                # Always close the response
                                response.close()
                            else:
                                print(f"HEAD request failed with status {head_response.status_code}")
                                head_response.close()
                            
                        except requests.exceptions.RequestException as e:
                            print(f"Error accessing {test_url}: {str(e)}")
                            # Wait before retrying
                            time.sleep(3)
                    
                if server_ready:
                    break
                
            
            # If we found a working URL, update the tasks
            if server_ready and working_url:
                # Update task URLs to use the working URL
                for task in tasks:
                    if 'web_name' in task and task['web_name'].startswith(app_id):
                        if 'web' in task and task['web'] != working_url:
                            print(f"Updating task URL from {task['web']} to {working_url}")
                            task['web'] = working_url
                            updated_tasks = True
            
            # If we couldn't get the server running or verify it, return error
            if not server_ready:
                print(f"Error: Could not verify React app for {app_id}")
                print("Please ensure the React app is properly built and the server is running before starting WebVoyager.")
                return
        
        # Save updated tasks if any URLs were changed
        if updated_tasks:
            print("Updating tasks file with correct URLs...")
            save_jsonl(tasks, tasks_file)
                
        print("All React servers are running. Starting WebVoyager...")
    except Exception as e:
        print(f"Error checking React servers: {str(e)}")
        print("Cannot continue with WebVoyager due to server issues.")
        return
    
    # Create a simplified task file specifically for WebVoyager
    # This ensures we're using the correct port
    app_id = next(iter(ports))  # Get the first app ID
    port = ports[app_id]        # Get its port

    # Verify one more time that the server is accessible before starting WebVoyager
    print(f"Performing final verification of React server on port {port}...")
    try:
        # Use a simple HEAD request to check server availability
        session = requests.Session()
        session.headers['Connection'] = 'close'  # Disable keep-alive
        response = session.head(f"http://localhost:{port}/", timeout=5)
        if response.status_code == 200:
            print(f"React server confirmed accessible on port {port}")
        else:
            print(f"Warning: React server returned status code {response.status_code}")
    except Exception as e:
        print(f"Warning: Could not verify React server in final check: {str(e)}")
        print("Continuing anyway...")
    

    # Convert all path objects to strings to avoid TypeError
    tasks_file_str = str(tasks_file) if isinstance(tasks_file, Path) else tasks_file
    ports_file_str = str(ports_file) if isinstance(ports_file, Path) else ports_file
    output_dir_str = f'{base_dir}/results_{formatted_output_folder}/results/{data_src}'
    download_dir_str = f'{base_dir}/results_{formatted_output_folder}/download/{data_src}'
    
    cmd = [
        sys.executable,              # equivalent to "python"
        "-u", "{base_dir}/webvoyager/run.py",    # use forward slash for Linux
        "--test_file", tasks_file_str,
        "--ports_file", ports_file_str,  # Add ports file
        "--api_key", "",  # OpenRouter API key
        "--api_model", "qwen/qwen2.5-vl-72b-instruct",
        "--headless",
        "--max_iter", "15",
        "--max_attached_imgs", "3",
        "--temperature", "1",
        "--fix_box_color",
        "--seed", "42", 
        "--output_dir", output_dir_str,
        "--download_dir", download_dir_str,
        "--num_workers", f"{num_of_tasks}",
    ]

    # Set up environment variables for WebVoyager
    env = os.environ.copy()
    webvoyager_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'webvoyager'))
    env['PYTHONPATH'] = f"{webvoyager_dir}:{env.get('PYTHONPATH', '')}"  # Add webvoyager to PYTHONPATH
    
    # Run the command with better error handling and timeouts
    print(f"Running WebVoyager with command: {' '.join(cmd)}")
    print(f"Using PYTHONPATH: {env.get('PYTHONPATH', 'Not set')}")
    print(f"Working directory: {webvoyager_dir}")
    print(f"Tasks will be executed sequentially for better reliability")
    
    # Save current directory
    original_dir = os.getcwd()
    
    try:
        # Set a longer timeout for the entire process (30 minutes)
        timeout_seconds = 1800        
        # Use subprocess.Popen to get real-time output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env,
            cwd=webvoyager_dir  # Run from the webvoyager directory
        )
        
        # Print output in real-time with timeout handling
        start_time = time.time()
        output_lines = []
        
        while process.poll() is None:
            # Check if we've exceeded the timeout
            if time.time() - start_time > timeout_seconds:
                print(f"WebVoyager process timed out after {timeout_seconds} seconds")
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()
                break
                
            # Read output with a short timeout to allow checking the process status
            try:
                line = process.stdout.readline()
                if line:
                    print(line, end='')
                    output_lines.append(line)
                else:
                    # No output available, sleep briefly
                    time.sleep(0.1)
            except Exception as e:
                print(f"Error reading output: {e}")
                time.sleep(0.5)
        
        # Get any remaining output
        remaining_output, _ = process.communicate()
        if remaining_output:
            print(remaining_output, end='')
            output_lines.append(remaining_output)        
            
        if process.returncode != 0:
            print(f"WebVoyager process failed with return code {process.returncode}")
        else:
            print("WebVoyager completed successfully")
            
    except subprocess.TimeoutExpired:
        print("WebVoyager process timed out")
        if 'process' in locals():
            process.terminate()
            time.sleep(1)
            if process.poll() is None:
                process.kill()
    except Exception as e:
        print(f"Unexpected error running WebVoyager: {type(e).__name__}: {e}")
        traceback.print_exc()
    finally:
        # Always restore original directory
        os.chdir(original_dir)


    

def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--base_dir", type=str, help="Base DIR path")
    parser.add_argument("--data_src", type=str, help="Input data src (e.g., llama4)")
    parser.add_argument("--case_id", type=str, help="Case ID to evaluate (e.g., 000001)")
    parser.add_argument("--port", type=int, help="Preferred port for the specified project")
    parser.add_argument("--preferred_ports", type=str, help="JSON file with preferred ports mapping {project_id: port_number}")
    parser.add_argument("--formatted_output_folder", type=str, help="Input web data src (e.g., webgen_formatted)")
    args = parser.parse_args()

    
    base_dir=args.base_dir
                 
    if os.path.exists(f'{base_dir}/results_{args.formatted_output_folder}/extract/{args.data_src}'):
      
        
        # Get preferred port if specified
        preferred_port = None
        if args.port:
            preferred_port = args.port
            print(f"Using port {preferred_port}")

                # Get preferred port if specified
        sample_id = None
        if args.case_id:
            sample_id = args.case_id + "-1"
            
        httpd, port, server_thread = launch_react_project(os.path.join(f'{base_dir}/results_{args.formatted_output_folder}/extract/{args.data_src}', sample_id, 'out'), preferred_port)
        if httpd is None or port is None:
            print("Failed to start React project")
    
            
        try:
            # Start evaluation part   
            output_root = f'{base_dir}/results_{args.formatted_output_folder}/results/{args.data_src}'
            full_path = os.path.abspath(output_root)
            print(f"Current working directory: {os.getcwd()}")
            print(f"Looking for results folder at: {full_path}")
            if not os.path.exists(output_root):
                print('Folder does not exist, creating it...')
                os.makedirs(output_root, exist_ok=True)
                print(f'Created directory: {full_path}')
            else: 
                print(f'Results folder already exists at: {full_path}')
                print(f'Contents of {full_path}: {os.listdir(full_path) if os.path.exists(full_path) else "Directory not found"}')

            print("\nStarting evaluation...")
            # tasks_file = os.path.join(output_root, "tasks_test_with_answer.jsonl")
            ports = {}
            ports[sample_id] = port
            print('PORTS!!!!! ', ports)
            filtered_dir = f'{base_dir}/tasks/general_webui/'
            _ = process_all_formatted_test_responses(filtered_dir, output_root, args.case_id, "1")
            
            # Save port to file for webvoyager - overwrite with just the current sample_id
            ports_file = os.path.join(output_root, "ports.json")
            
            # Create a new ports dictionary with only the current sample_id
            # This ensures we don't have any conflicts with previous port assignments
            new_ports = {}
            new_ports[sample_id] = port
            
            # Write the new ports dictionary to the file, overwriting any existing content
            print(f"Writing new port assignment: {sample_id} -> {port} to {ports_file}")

            
            # Save updated ports
            with open(ports_file, "w") as f:
                json.dump(new_ports, f, indent=2)
            print(f"Saved port {port} for sample {sample_id} to {ports_file}")
                
            # Run webvoyager tests with the correct port
            print(f"\nRunning WebVoyager tests on port {port}...")
            # Wait a bit longer for React app to fully initialize
            print(f"Waiting 15 seconds for React app to fully initialize on port {port}...")
            time.sleep(15)
            
            try:
                # Run WebVoyager for this task
                task_file_str = os.path.join(output_root, f'test_tasks_{sample_id}.jsonl')
                run_webvoyager(output_root, port_file_path=ports_file, task_file_path=task_file_str, data_src=args.data_src, formatted_output_folder=args.formatted_output_folder)
                print(f"\nEvaluation for sample {sample_id} completed successfully!")
            finally:
                # Always ensure server is shut down after task completes
                print("\nShutting down server after task completion...")
                if httpd:
                    try:
                        httpd.shutdown()
                        httpd.server_close()
                        print(f"Server on port {port} has been stopped")
                    except Exception as e:
                        print(f"Error shutting down server: {e}")
                    
                # Kill any remaining processes using this port
                kill_process_on_port(port)
                
                # Wait a moment to ensure port is fully released
                time.sleep(3)
            
                
        except Exception as e:
            print(f"\nError during evaluation: {e}")
            
        finally:
            # Clean up
            print("\nFinal cleanup...")
            
            # Server should already be shut down in the inner try-finally block,
            # but do a final check to make sure the port is free
            print("Performing final port cleanup...")
            try:
                # Make sure no processes are still using the port
                kill_process_on_port(port)
            except Exception as e:
                print(f"Error during final port cleanup: {e}")
            
            # Clean up PM2 processes
            print("Stopping PM2 processes...")
            subprocess.run("pm2 delete all", shell=True)
            
            # Change back to original directory
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
            print("Cleanup completeds.")
            
            # Wait a moment to ensure all resources are released
            time.sleep(2)
    else:
        print('file not exists')



if __name__ == "__main__":
    main()