"""
Starter script for BMP to PNG Converter
This script checks for required dependencies and launches the main application
"""
import os
import sys
import subprocess
import importlib.util
import time

# Welcome message
WELCOME_MESSAGE = """
╔══════════════════════════════════════════════════════════════════╗
║                    BMP to PNG Converter v1.0                     ║
║                                                                  ║
║  Welcome to the BMP to PNG Converter!                            ║
║  This tool will help you convert BMP files to PNG format,        ║
║  with optional transparency for a specified color.               ║
║                                                                  ║
║  Instructions:                                                   ║
║  1. Click 'Select Folder' to choose your BMP files               ║
║  2. Wait for the conversion to complete                          ║
║  3. Find your converted files in the 'PNG_exports' folder        ║
║                                                                  ║
║  Created by: Vexx                                                ║
╚══════════════════════════════════════════════════════════════════╝
"""

# Set up paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_DIR = os.path.join(BASE_DIR, "python_embedded")
PYTHON_EXE = os.path.join(PYTHON_DIR, "python.exe")
MAIN_APP = os.path.join(BASE_DIR, "app.py")

def log(message, error=False):
    """Print a timestamped log message"""
    timestamp = time.strftime('%H:%M:%S')
    if error:
        print(f"[{timestamp}] ERROR: {message}")
        input("Press Enter to exit...")  # Replace pause functionality
        sys.exit(1)
    else:
        print(f"[{timestamp}] {message}")

# Check if Python executable exists
if not os.path.exists(PYTHON_EXE):
    log("Embedded Python not found at " + PYTHON_EXE, error=True)

print(WELCOME_MESSAGE)

# Configure Python path
sys.path.insert(0, BASE_DIR)
os.environ["PATH"] = PYTHON_DIR + os.pathsep + os.environ.get("PATH", "")

def check_module(module_name):
    """Check if a module is available"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def install_package(package_name):
    """Install a package using pip"""
    log(f"Installing {package_name}...")
    pip_cmd = [sys.executable, "-m", "pip", "install", package_name, "--no-warn-script-location"]
    
    try:
        subprocess.check_call(pip_cmd)
        log(f"Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        log(f"Failed to install {package_name}: {e}")
        return False

def setup_environment():
    """Set up the Python environment with required packages"""
    log("Setting up environment...")
    
    # Check and enable site-packages if needed
    pth_file = None
    for file in os.listdir(PYTHON_DIR):
        if file.endswith("._pth"):
            pth_file = os.path.join(PYTHON_DIR, file)
            break
    
    if pth_file:
        with open(pth_file, 'r') as f:
            content = f.read()
        
        if '#import site' in content:
            log("Enabling site-packages...")
            with open(pth_file, 'w') as f:
                f.write(content.replace('#import site', 'import site'))
            log("Site-packages enabled. Restarting script...")
            # Restart the script to apply changes
            os.execv(sys.executable, [sys.executable] + sys.argv)
    
    # Check for pip
    if not check_module("pip"):
        log("Pip not available. Installing pip...")
        get_pip_path = os.path.join(PYTHON_DIR, "get-pip.py")
        
        if not os.path.exists(get_pip_path):
            import urllib.request
            log("Downloading get-pip.py...")
            urllib.request.urlretrieve(
                "https://bootstrap.pypa.io/get-pip.py", 
                get_pip_path
            )
        
        subprocess.check_call([sys.executable, get_pip_path, "--no-warn-script-location"])
        log("Pip installed successfully")
    
    # Check for required packages
    required_packages = ["pillow"]
    for package in required_packages:
        if not check_module(package.split("==")[0].replace("-", "_")):
            if not install_package(package):
                log(f"Failed to install required package: {package}", error=True)
    
    # Check for tkinter - this is built-in and can't be installed via pip
    if not check_module("tkinter"):
        log("tkinter is not available. The GUI will not work.\ntkinter must be included with your Python installation.\nYou may need to install a full version of Python or manually copy tkinter files.", error=True)
    
    return True

def run_main_app():
    """Run the main application"""
    log("Starting application...")
    try:
        subprocess.check_call([sys.executable, MAIN_APP])
        return True
    except subprocess.CalledProcessError as e:
        log(f"Application failed to start: {e}", error=True)
        return False

if __name__ == "__main__":
    log("Initializing...")
    
    if setup_environment():
        log("Environment setup complete")
        success = run_main_app()
        if success:
            log("Application completed successfully")
        else:
            log("Application failed", error=True)
    else:
        log("Failed to set up environment", error=True)
    
    log("Exiting")