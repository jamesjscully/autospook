#!/usr/bin/env python3
"""
AutoSpook OSINT Development Launcher
Runs both frontend and backend services with combined logging in a single terminal
"""

import subprocess
import threading
import time
import signal
import sys
import os
from datetime import datetime
import queue
import select

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class DevLauncher:
    def __init__(self):
        self.processes = []
        self.log_queue = queue.Queue()
        self.running = True
        self.frontend_port = "5173"  # Default, will be detected
        
    def log(self, service, message, color=Colors.ENDC):
        """Add timestamped log message to queue"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"{color}[{timestamp}] {service:10} | {message}{Colors.ENDC}"
        self.log_queue.put(formatted)
        
    def print_logs(self):
        """Print logs from queue in real-time"""
        while self.running:
            try:
                message = self.log_queue.get(timeout=0.1)
                print(message)
            except queue.Empty:
                continue
                
    def run_process(self, cmd, cwd, service_name, color):
        """Run a process and capture its output"""
        try:
            self.log("LAUNCHER", f"Starting {service_name}...", Colors.CYAN)
            
            # Start process
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append(process)
            
            # Read stdout in separate thread
            def read_stdout():
                while process.poll() is None:
                    try:
                        line = process.stdout.readline()
                        if line:
                            self.log(service_name, line.strip(), color)
                    except:
                        break
                        
            # Read stderr in separate thread  
            def read_stderr():
                while process.poll() is None:
                    try:
                        line = process.stderr.readline()
                        if line:
                            stripped = line.strip()
                            # Detect if it's actually an error or just normal logging
                            if any(level in stripped for level in ["INFO:", "DEBUG:", "WARNING:"]):
                                # Normal log message that went to stderr
                                self.log(service_name, stripped, color)
                            elif any(error_word in stripped.lower() for error_word in ["error", "exception", "traceback", "failed"]):
                                # Actual error
                                self.log(service_name, f"ERROR: {stripped}", Colors.RED)
                            else:
                                # Unknown stderr output, mark as warning
                                self.log(service_name, f"STDERR: {stripped}", Colors.YELLOW)
                    except:
                        break
                        
            threading.Thread(target=read_stdout, daemon=True).start()
            threading.Thread(target=read_stderr, daemon=True).start()
            
            return process
            
        except Exception as e:
            self.log("LAUNCHER", f"Failed to start {service_name}: {e}", Colors.RED)
            return None
            
    def check_prerequisites(self):
        """Check if required files and directories exist"""
        self.log("LAUNCHER", "Checking prerequisites...", Colors.CYAN)
        
        # Check directories
        if not os.path.exists("backend"):
            self.log("LAUNCHER", "❌ backend directory not found", Colors.RED)
            return False
            
        if not os.path.exists("frontend"):
            self.log("LAUNCHER", "❌ frontend directory not found", Colors.RED)
            return False
            
        # Check backend files
        if not os.path.exists("backend/simple_api.py"):
            self.log("LAUNCHER", "❌ backend/simple_api.py not found", Colors.RED)
            return False
            
        # Check frontend files
        if not os.path.exists("frontend/package.json"):
            self.log("LAUNCHER", "❌ frontend/package.json not found", Colors.RED)
            return False
            
        self.log("LAUNCHER", "✅ All prerequisites found", Colors.GREEN)
        return True
        
    def start_services(self):
        """Start all development services"""
        
        # Start backend API
        backend_cmd = [sys.executable, "-m", "uvicorn", "simple_api:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
        backend_process = self.run_process(
            backend_cmd, 
            "backend", 
            "BACKEND", 
            Colors.BLUE
        )
        
        if not backend_process:
            return False
            
        # Wait for backend to start
        self.log("LAUNCHER", "Waiting for backend to start...", Colors.CYAN)
        time.sleep(3)
        
        # Start frontend
        frontend_cmd = ["npm", "run", "dev"]
        frontend_process = self.run_process(
            frontend_cmd,
            "frontend", 
            "FRONTEND", 
            Colors.GREEN
        )
        
        if not frontend_process:
            return False
            
        # Wait for frontend to start
        self.log("LAUNCHER", "Waiting for frontend to start...", Colors.CYAN)
        time.sleep(5)
        
        return True
        
    def test_services(self):
        """Test if services are responding"""
        self.log("LAUNCHER", "Testing services...", Colors.CYAN)
        
        # Test backend
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                self.log("LAUNCHER", "✅ Backend API responding", Colors.GREEN)
            else:
                self.log("LAUNCHER", f"⚠️ Backend API returned status {response.status_code}", Colors.YELLOW)
        except Exception as e:
            self.log("LAUNCHER", f"❌ Backend API not responding: {e}", Colors.RED)
            
        # Test frontend (detect actual port)
        import socket
        frontend_found = False
        for port in [5173, 5174, 5175, 5176, 5177]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                if result == 0:
                    self.frontend_port = str(port)
                    self.log("LAUNCHER", f"✅ Frontend service responding on port {port}", Colors.GREEN)
                    frontend_found = True
                    break
            except Exception as e:
                continue
                
        if not frontend_found:
            self.log("LAUNCHER", "❌ Frontend service not responding on any port", Colors.RED)
            
    def show_access_info(self):
        """Show access information"""
        # Use the detected frontend port from test_services
                
        self.log("LAUNCHER", "=" * 60, Colors.HEADER)
        self.log("LAUNCHER", "🚀 AutoSpook OSINT Development Environment Ready!", Colors.HEADER)
        self.log("LAUNCHER", "=" * 60, Colors.HEADER)
        self.log("LAUNCHER", "", Colors.ENDC)
        self.log("LAUNCHER", f"📱 Frontend:     http://localhost:{self.frontend_port}/app/", Colors.GREEN)
        self.log("LAUNCHER", "🔧 Backend API:  http://localhost:8000", Colors.BLUE)
        self.log("LAUNCHER", "📚 API Docs:     http://localhost:8000/docs", Colors.BLUE)
        self.log("LAUNCHER", "💚 Health Check: http://localhost:8000/health", Colors.BLUE)
        self.log("LAUNCHER", "", Colors.ENDC)
        self.log("LAUNCHER", "🧪 Test Investigation:", Colors.YELLOW)
        self.log("LAUNCHER", f"  1. Open http://localhost:{self.frontend_port}/app/", Colors.YELLOW)
        self.log("LAUNCHER", "  2. Enter query: 'Ali Khaledi Nasab'", Colors.YELLOW)
        self.log("LAUNCHER", "  3. Click 'Start Investigation'", Colors.YELLOW)
        self.log("LAUNCHER", "  4. Watch mock results appear!", Colors.YELLOW)
        self.log("LAUNCHER", "", Colors.ENDC)
        self.log("LAUNCHER", "Press Ctrl+C to stop all services", Colors.CYAN)
        self.log("LAUNCHER", "=" * 60, Colors.HEADER)
        
    def cleanup(self):
        """Clean up processes"""
        self.log("LAUNCHER", "Shutting down services...", Colors.CYAN)
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except:
                pass
                
        self.log("LAUNCHER", "✅ All services stopped", Colors.GREEN)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.running = False
        self.cleanup()
        sys.exit(0)
        
    def run(self):
        """Main run method"""
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start log printer thread
        log_thread = threading.Thread(target=self.print_logs, daemon=True)
        log_thread.start()
        
        # Show header
        self.log("LAUNCHER", "=" * 60, Colors.HEADER)
        self.log("LAUNCHER", "🕵️ AutoSpook OSINT Development Launcher", Colors.HEADER)
        self.log("LAUNCHER", "=" * 60, Colors.HEADER)
        
        # Check prerequisites
        if not self.check_prerequisites():
            self.log("LAUNCHER", "❌ Prerequisites check failed", Colors.RED)
            sys.exit(1)
            
        # Start services
        if not self.start_services():
            self.log("LAUNCHER", "❌ Failed to start services", Colors.RED)
            sys.exit(1)
            
        # Test services
        self.test_services()
        
        # Show access info
        self.show_access_info()
        
        # Keep running and showing logs
        stopped_processes = set()
        try:
            while self.running:
                # Check if any process has died (only report once)
                for process in self.processes:
                    if process.poll() is not None and process.pid not in stopped_processes:
                        self.log("LAUNCHER", f"⚠️ Process {process.pid} has stopped", Colors.YELLOW)
                        stopped_processes.add(process.pid)
                        
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

if __name__ == "__main__":
    # Install requests if not available
    try:
        import requests
    except ImportError:
        print("Installing requests...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    
    launcher = DevLauncher()
    launcher.run() 