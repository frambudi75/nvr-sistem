import os
import time
import logging

logger = logging.getLogger(__name__)

class Cleaner:
    def __init__(self, storage_path, retention_days):
        self.storage_path = storage_path
        self.retention_days = retention_days
        # Convert days to seconds
        self.retention_seconds = retention_days * 24 * 60 * 60

    def cleanup_old_files(self):
        """Scans the storage directory and deletes files older than retention_days."""
        if self.retention_days <= 0:
            return # Auto-delete is disabled

        logger.info("Starting cleanup of old files...")
        current_time = time.time()
        deleted_count = 0
        freed_space = 0

        # Walk through all directories inside storage_path
        for root, dirs, files in os.walk(self.storage_path):
            for file in files:
                if not file.endswith(".mp4"):
                    continue

                file_path = os.path.join(root, file)
                try:
                    # Get file modification time
                    mtime = os.path.getmtime(file_path)
                    age_seconds = current_time - mtime

                    if age_seconds > self.retention_seconds:
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                        freed_space += size
                        logger.debug(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error checking/deleting file {file_path}: {e}")
        
        if deleted_count > 0:
            freed_mb = freed_space / (1024 * 1024)
            logger.info(f"Cleanup finished. Deleted {deleted_count} files, freed {freed_mb:.2f} MB.")
        else:
            logger.info("Cleanup finished. No files needed deletion.")
