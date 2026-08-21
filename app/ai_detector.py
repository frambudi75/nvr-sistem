import cv2
import threading
import time
import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger("NVR-AI")

class AIDetector:
    def __init__(self, camera_config, storage_path, nvr_manager):
        self.camera_config = camera_config
        self.camera_id = camera_config.get('id')
        self.camera_name = camera_config.get('name')
        self.rtsp_url = camera_config.get('rtsp_url')
        self.storage_path = storage_path
        self.nvr_manager = nvr_manager
        
        self.alerts_dir = os.path.join(storage_path, self.camera_id, "alerts")
        os.makedirs(self.alerts_dir, exist_ok=True)
        
        self.running = False
        self.thread = None
        
        # Initialize HOG descriptor/person detector
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        self.last_alert_time = 0
        self.cooldown = 60 # seconds between discord alerts for the same camera

    def start(self):
        if not self.rtsp_url:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        logger.info(f"[{self.camera_name}] AI Detector started.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"[{self.camera_name}] AI Detector stopped.")

    def _process_loop(self):
        # We try to connect to the RTSP stream.
        cap = cv2.VideoCapture(self.rtsp_url)
        # Force low framerate capture if possible
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        consecutive_failures = 0

        while self.running:
            if not cap.isOpened():
                logger.warning(f"[{self.camera_name}] Reconnecting AI Stream...")
                cap.release()
                time.sleep(5)
                cap = cv2.VideoCapture(self.rtsp_url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                continue

            # Grab frames quickly to flush buffer, but only decode occasionally
            # to save CPU on this background task.
            for _ in range(15): # flush 15 frames
                cap.grab()
            
            ret, frame = cap.read()
            if not ret:
                consecutive_failures += 1
                if consecutive_failures > 5:
                    cap.release()
                time.sleep(1)
                continue
                
            consecutive_failures = 0
            
            try:
                # Resize to standard small size for faster HOG processing
                frame_resized = cv2.resize(frame, (640, 360))
                
                # Detect people in the image
                # (boxes, weights)
                boxes, weights = self.hog.detectMultiScale(frame_resized, winStride=(8, 8))
                
                if len(boxes) > 0:
                    # Filter boxes with weight > 0.5 to reduce false positives
                    valid_boxes = [box for i, box in enumerate(boxes) if weights[i] > 0.5]
                    
                    if valid_boxes:
                        now = time.time()
                        if now - self.last_alert_time > self.cooldown:
                            self.last_alert_time = now
                            self._handle_detection(frame, valid_boxes)
            except Exception as e:
                logger.error(f"[{self.camera_name}] AI Processing error: {e}")
                
            # Sleep a bit to keep CPU usage absolutely minimal (1 frame analyzed per 2 seconds)
            time.sleep(2)
            
        cap.release()

    def _handle_detection(self, original_frame, boxes):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logger.info(f"[{self.camera_name}] Human detected at {timestamp}!")
        
        # We need to map the boxes from 640x360 back to original resolution
        h, w = original_frame.shape[:2]
        scale_x = w / 640
        scale_y = h / 360
        
        # Draw boxes
        for (x, y, w_b, h_b) in boxes:
            x_orig, y_orig = int(x * scale_x), int(y * scale_y)
            w_orig, h_orig = int(w_b * scale_x), int(h_b * scale_y)
            cv2.rectangle(original_frame, (x_orig, y_orig), (x_orig + w_orig, y_orig + h_orig), (0, 255, 0), 3)
            cv2.putText(original_frame, 'Human', (x_orig, y_orig - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
        # Save snapshot
        filename = f"alert_{timestamp}.jpg"
        filepath = os.path.join(self.alerts_dir, filename)
        cv2.imwrite(filepath, original_frame)
        
        # Send Discord webhook if enabled
        dc_config = self.nvr_manager.config.get("notifications", {}).get("discord", {})
        if dc_config.get("enabled"):
            self._send_discord_webhook_with_image(dc_config.get("webhook_url"), filepath, timestamp)

    def _send_discord_webhook_with_image(self, webhook_url, filepath, timestamp):
        if not webhook_url:
            return
            
        try:
            with open(filepath, 'rb') as f:
                payload = {
                    "content": f"🚨 **[AI Alert]** Manusia terdeteksi di kamera **{self.camera_name}** pada {timestamp}!"
                }
                files = {
                    "file": (os.path.basename(filepath), f, "image/jpeg")
                }
                requests.post(webhook_url, data=payload, files=files, timeout=10)
        except Exception as e:
            logger.error(f"[{self.camera_name}] Failed to upload alert image to Discord: {e}")
