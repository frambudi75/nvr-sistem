import subprocess
import os
import time
import logging

logger = logging.getLogger(__name__)

class Recorder:
    def __init__(self, camera_config, storage_path, segment_time):
        self.camera_id = camera_config.get('id')
        self.camera_name = camera_config.get('name')
        self.rtsp_url = camera_config.get('rtsp_url')
        
        # Determine camera storage path
        self.cam_storage_path = os.path.join(storage_path, self.camera_id)
        os.makedirs(self.cam_storage_path, exist_ok=True)
        
        self.segment_time = segment_time
        self.process = None

    def start(self):
        if not self.rtsp_url:
            logger.error(f"[{self.camera_name}] No RTSP URL provided.")
            return

        logger.info(f"[{self.camera_name}] Starting recording...")

        # Output pattern for segmented files: e.g. 2026-08-13_18-40-00.mp4
        output_pattern = os.path.join(self.cam_storage_path, "%Y-%m-%d_%H-%M-%S.mp4")

        # FFmpeg command to pull RTSP and split into chunks
        # We use -c copy to copy the stream directly without re-encoding (saves CPU)
        command = [
            "ffmpeg",
            "-rtsp_transport", "tcp", # Use TCP for better reliability over RTSP
            "-i", self.rtsp_url,
            "-c", "copy",
            "-f", "segment",
            "-segment_time", str(self.segment_time),
            "-segment_format", "mp4",
            "-strftime", "1",
            "-reset_timestamps", "1",
            "-loglevel", "error", # Only log errors from ffmpeg to avoid spam
            output_pattern
        ]

        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"[{self.camera_name}] FFmpeg process started with PID {self.process.pid}")
        except Exception as e:
            logger.error(f"[{self.camera_name}] Failed to start FFmpeg: {e}")

    def stop(self):
        if self.process:
            logger.info(f"[{self.camera_name}] Stopping recording...")
            try:
                if self.process.stdin:
                    # Write 'q' to stdin to tell ffmpeg to stop and close output files gracefully
                    self.process.stdin.write(b'q\n')
                    self.process.stdin.flush()
                self.process.wait(timeout=5)
            except Exception as e:
                logger.warning(f"[{self.camera_name}] Graceful stop failed: {e}. Falling back to terminate.")
                try:
                    self.process.terminate()
                    self.process.wait(timeout=3)
                except Exception:
                    self.process.kill()
            self.process = None
            logger.info(f"[{self.camera_name}] Recording stopped.")

    def check_health(self):
        """Check if the ffmpeg process is still running."""
        if self.process is None:
            return False
        
        # poll() returns None if process is running, otherwise exit code
        if self.process.poll() is not None:
            logger.warning(f"[{self.camera_name}] FFmpeg process died unexpectedly. Exit code: {self.process.poll()}")
            self.process = None
            return False
        return True
