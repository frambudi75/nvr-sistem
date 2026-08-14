import json
import logging
import os
import sys
import time
import threading
from recorder import Recorder
from cleanup import Cleaner
from web import start_web_server
from notifier import send_notification

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
        self.camera_states = {} # dict of camera_id -> state ("online" or "offline")
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
                # On Windows, if storage_path is set to an absolute-like Linux path (e.g. /recordings),
                # map it to a relative workspace folder so files are written and served inside the project directory.
                if os.name == 'nt' and (self.storage_path.startswith('/') or self.storage_path.startswith('\\')):
                    self.storage_path = os.path.join(os.path.dirname(self.config_path), self.storage_path.lstrip('/\\'))
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
                if cam_id in self.camera_states:
                    del self.camera_states[cam_id]
        
        # Start new recorders
        for cam_id, cam in cameras_config.items():
            if cam.get("enabled", True) and cam_id not in self.recorders:
                recorder = Recorder(cam, self.storage_path, self.segment_time)
                self.recorders[cam_id] = recorder
                recorder.start()
                self.camera_states[cam_id] = "online"
                
    def reload_config(self):
        """Called by Web UI after config is updated."""
        logger.info("Reloading configuration...")
        self.load_config()
        self.sync_cameras()
        # Note: Retention change won't affect running cleaner immediately in this basic version,
        # but it will pick it up eventually or we can recreate the cleaner.

    def monitor_health(self):
        for cam_id, recorder in self.recorders.items():
            is_healthy = recorder.check_health()
            prev_state = self.camera_states.get(cam_id, "online")
            
            if not is_healthy:
                if prev_state == "online":
                    # State changed to offline
                    self.camera_states[cam_id] = "offline"
                    msg = f"⚠️ <b>[NVR Alert]</b> Kamera <b>{recorder.camera_name}</b> ({cam_id}) terputus/offline! Mencoba menghubungkan kembali..."
                    logger.warning(msg)
                    send_notification(self.config, msg)
                
                logger.warning(f"Camera {recorder.camera_name} down. Restarting...")
                recorder.start()
            else:
                if prev_state == "offline":
                    # State changed back to online
                    self.camera_states[cam_id] = "online"
                    msg = f"✅ <b>[NVR Alert]</b> Kamera <b>{recorder.camera_name}</b> ({cam_id}) terhubung kembali (online)."
                    logger.info(msg)
                    send_notification(self.config, msg)


def cleanup_worker(nvr_manager, interval=600):
    while True:
        try:
            # 1. Retention Days Cleanup
            retention_days = nvr_manager.config.get("retention_days", 7)
            if retention_days > 0:
                cleaner = Cleaner(nvr_manager.storage_path, retention_days)
                cleaner.cleanup_old_files()
                
            # 2. Smart Storage Purge
            smart_config = nvr_manager.config.get("smart_cleanup", {})
            min_free_gb = smart_config.get("min_free_gb", 5)
            
            if min_free_gb > 0:
                import shutil
                total, used, free = shutil.disk_usage(nvr_manager.storage_path)
                free_gb = free / (1024**3)
                
                if free_gb < min_free_gb:
                    logger.warning(f"Free storage ({free_gb:.2f} GB) is below minimum threshold ({min_free_gb} GB). Starting smart cleanup...")
                    
                    # Gather all MP4 files with their modified times
                    mp4_files = []
                    for root, dirs, files in os.walk(nvr_manager.storage_path):
                        for file in files:
                            if file.endswith(".mp4"):
                                file_path = os.path.join(root, file)
                                try:
                                    mtime = os.path.getmtime(file_path)
                                    size = os.path.getsize(file_path)
                                    mp4_files.append((file_path, mtime, size))
                                except Exception:
                                    continue
                                    
                    # Sort by modified time (oldest first)
                    mp4_files.sort(key=lambda x: x[1])
                    
                    deleted_count = 0
                    freed_space = 0
                    
                    for file_path, mtime, size in mp4_files:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                            freed_space += size
                            logger.info(f"Smart Cleanup deleted oldest file: {file_path}")
                            
                            # Re-evaluate free space
                            total, used, free = shutil.disk_usage(nvr_manager.storage_path)
                            free_gb = free / (1024**3)
                            
                            if free_gb >= (min_free_gb + 2): # Safety margin
                                break
                        except Exception as e:
                            logger.error(f"Failed to delete {file_path} during smart cleanup: {e}")
                            
                    if deleted_count > 0:
                        freed_mb = freed_space / (1024 * 1024)
                        msg = f"⚠️ <b>[NVR Storage Warning]</b> Kapasitas penyimpanan bebas ({free_gb:.2f} GB) berada di bawah batas minimum ({min_free_gb} GB). Smart Cleanup menghapus {deleted_count} rekaman tertua untuk membebaskan {freed_mb:.2f} MB."
                        logger.warning(msg)
                        send_notification(nvr_manager.config, msg)
        except Exception as e:
            logger.error(f"Error in cleanup worker: {e}")
        time.sleep(interval)


def main():
    logger.info("Starting NVR Engine...")
    
    config_path = os.environ.get("CONFIG_PATH", NVRManager.get_default_config_path())
    logger.info(f"Using config file at: {config_path}")
    
    nvr = NVRManager(config_path)
    nvr.sync_cameras()

    # Start cleanup thread (runs every 10 minutes / 600s)
    cleanup_thread = threading.Thread(target=cleanup_worker, args=(nvr, 600), daemon=True)
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
