import json
import logging
import os
import sys
import time
import threading
from recorder import Recorder
from cleanup import Cleaner
from web import start_web_server

# Configure logging
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'nvr.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file_path)
    ]
)
logger = logging.getLogger("NVR-Main")

class NVRManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = {}
        self.recorders = {} # dict of camera_id -> Recorder
        self.storage_path = "/recordings"
        self.segment_time = 900
        self.cleaner = None
        
        self.load_config()

    def get_default_config_path():
        # Defaults to parent directory of the 'app' folder
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
                self.storage_path = self.config.get("storage_path", os.path.join(os.path.dirname(self.config_path), "recordings"))
                self.segment_time = self.config.get("segment_time", 900)
                os.makedirs(self.storage_path, exist_ok=True)
                return True
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            # Initialize empty config to not crash completely
            self.config = {"cameras": []}
            return False

    def save_config(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")
            return False

    def sync_cameras(self):
        """Starts/stops recorders based on current config."""
        cameras_config = {cam["id"]: cam for cam in self.config.get("cameras", [])}
        
        # Stop recorders that are no longer in config or disabled
        for cam_id, recorder in list(self.recorders.items()):
            if cam_id not in cameras_config or not cameras_config[cam_id].get("enabled", True):
                recorder.stop()
                del self.recorders[cam_id]
        
        # Start new recorders
        for cam_id, cam in cameras_config.items():
            if cam.get("enabled", True) and cam_id not in self.recorders:
                recorder = Recorder(cam, self.storage_path, self.segment_time)
                self.recorders[cam_id] = recorder
                recorder.start()
                
    def reload_config(self):
        """Called by Web UI after config is updated."""
        logger.info("Reloading configuration...")
        self.load_config()
        self.sync_cameras()
        # Note: Retention change won't affect running cleaner immediately in this basic version,
        # but it will pick it up eventually or we can recreate the cleaner.

    def monitor_health(self):
        for recorder in self.recorders.values():
            if not recorder.check_health():
                logger.warning(f"Camera {recorder.camera_name} down. Restarting...")
                recorder.start()


def cleanup_worker(nvr_manager, interval=3600):
    while True:
        try:
            retention_days = nvr_manager.config.get("retention_days", 7)
            if retention_days > 0:
                cleaner = Cleaner(nvr_manager.storage_path, retention_days)
                cleaner.cleanup_old_files()
        except Exception as e:
            logger.error(f"Error in cleanup worker: {e}")
        time.sleep(interval)


def main():
    logger.info("Starting NVR Engine...")
    
    config_path = os.environ.get("CONFIG_PATH", NVRManager.get_default_config_path())
    logger.info(f"Using config file at: {config_path}")
    
    nvr = NVRManager(config_path)
    nvr.sync_cameras()

    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_worker, args=(nvr, 3600), daemon=True)
    cleanup_thread.start()

    # Start Web Server in a daemon thread
    web_thread = threading.Thread(target=start_web_server, args=(nvr, 5000), daemon=True)
    web_thread.start()

    try:
        while True:
            nvr.monitor_health()
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Received exit signal. Shutting down...")
    finally:
        for recorder in nvr.recorders.values():
            recorder.stop()
        logger.info("NVR Engine stopped.")

if __name__ == "__main__":
    main()
