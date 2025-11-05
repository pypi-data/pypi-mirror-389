import os
import sys
import time
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('auto_live_reload')

class LiveReload:
    """Simple live reload functionality."""
    
    def __init__(self, patterns=None, delay=2):
        """Initialize the live reload watcher.
        
        Args:
            patterns (list): File patterns to watch (e.g., ['*.py', '*.html'])
            delay (int): Initial delay before starting to watch
        """
        self.patterns = patterns or ['*.py']
        self.delay = delay
        self.last_mtimes = {}
        self.files = []
        
    def watch_files(self):
        """Monitor files for changes and restart if modified."""
        logger.info(f"Starting live reload watcher with patterns: {self.patterns}")
        
        # Get the main script path to exclude it from watching
        main_script = os.path.abspath(sys.argv[0])
        
        time.sleep(self.delay)  # Initial delay
        
        # Initialize file list and modification times
        for root, _, filenames in os.walk('.'):
            for filename in filenames:
                if any(filename.endswith(pattern.replace('*', '')) for pattern in self.patterns):
                    file_path = os.path.join(root, filename)
                    self.files.append(file_path)
        
        # Set initial modification times
        self.last_mtimes = {f: os.stat(f).st_mtime for f in self.files if os.path.exists(f)}
        
        while True:
            try:
                # Check for changes
                for file_path in self.files:
                    if not os.path.exists(file_path):
                        continue
                    
                    # Skip the main script file to avoid infinite restart loop
                    abs_file_path = os.path.abspath(file_path)
                    if abs_file_path == main_script:
                        continue
                        
                    mtime = os.stat(file_path).st_mtime
                    if mtime != self.last_mtimes.get(file_path, 0):
                        logger.info(f"File changed: {file_path}")
                        logger.info("Restarting...")
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                
                # Update modification times
                self.last_mtimes = {f: os.stat(f).st_mtime for f in self.files if os.path.exists(f)}
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in watcher: {e}")
                time.sleep(1)

def start_auto_live_reload(patterns=None, delay=2):
    """Start the live reload watcher in a daemon thread.
    
    Args:
        patterns (list): File patterns to watch (e.g., ['*.py', '*.html'])
        delay (int): Initial delay before starting to watch
    """
    watcher = LiveReload(patterns=patterns, delay=delay)
    watcher_thread = threading.Thread(target=watcher.watch_files, daemon=True)
    watcher_thread.start()
