import subprocess
import os
import time
import logging
from datetime import datetime, timedelta

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
        self.log_file = None

    def _cleanup_process(self):
        """Safely reap any old/zombie FFmpeg process and close log handles."""
        if self.process is not None:
            try:
                exit_code = self.process.poll()
                if exit_code is not None:
                    # Process already dead — reap it via wait() to prevent zombie
                    try:
                        self.process.wait(timeout=2)
                    except Exception:
                        pass
                else:
                    # Still running — kill it first
                    try:
                        self.process.terminate()
                        self.process.wait(timeout=3)
                    except Exception:
                        try:
                            self.process.kill()
                            self.process.wait(timeout=2)
                        except Exception:
                            pass
            except Exception as e:
                logger.warning(f"[{self.camera_name}] Cleanup error: {e}")
            finally:
                self.process = None

        if self.log_file is not None:
            try:
                self.log_file.close()
            except Exception:
                pass
            self.log_file = None

    def start(self):
        if not self.rtsp_url:
            logger.error(f"[{self.camera_name}] No RTSP URL provided.")
            return

        # Always clean up old process/handles before starting a new one
        self._cleanup_process()

        logger.info(f"[{self.camera_name}] Starting recording...")

        # Output pattern for segmented files: e.g. 2026-08-13_18-40-00.mp4
        output_pattern = os.path.join(self.cam_storage_path, "%Y-%m-%d_%H-%M-%S.mp4")

        # FFmpeg command to pull RTSP and split into chunks
        command = [
            "ffmpeg",
            "-rtsp_transport", "tcp",
            "-i", self.rtsp_url,
            "-c", "copy",
            "-f", "segment",
            "-segment_time", str(self.segment_time),
            "-segment_format", "mp4",
            "-segment_format_options", "movflags=frag_keyframe+empty_moov",
            "-strftime", "1",
            "-reset_timestamps", "1",
            "-loglevel", "warning",
            output_pattern
        ]

        try:
            self.log_file = open(os.path.join(self.cam_storage_path, "ffmpeg.log"), "w")
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self.log_file
            )
            logger.info(f"[{self.camera_name}] FFmpeg process started with PID {self.process.pid}")
        except Exception as e:
            logger.error(f"[{self.camera_name}] Failed to start FFmpeg: {e}")
            self._cleanup_process()

    def stop(self):
        if self.process:
            logger.info(f"[{self.camera_name}] Stopping recording...")
            try:
                if self.process.stdin:
                    self.process.stdin.write(b'q\n')
                    self.process.stdin.flush()
                self.process.wait(timeout=5)
            except Exception as e:
                logger.warning(f"[{self.camera_name}] Graceful stop failed: {e}. Falling back to terminate.")
                try:
                    self.process.terminate()
                    self.process.wait(timeout=3)
                except Exception:
                    try:
                        self.process.kill()
                        self.process.wait(timeout=2)
                    except Exception:
                        pass
            self.process = None
            if self.log_file:
                try:
                    self.log_file.close()
                except Exception:
                    pass
                self.log_file = None
            logger.info(f"[{self.camera_name}] Recording stopped.")

    def check_health(self):
        """Check if the ffmpeg process is still running."""
        if self.process is None:
            return False
        
        exit_code = self.process.poll()
        if exit_code is not None:
            logger.warning(f"[{self.camera_name}] FFmpeg process died unexpectedly. Exit code: {exit_code}")
            # Reap zombie via wait() and cleanup handles
            self._cleanup_process()
            return False
        return True
