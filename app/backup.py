import os
import time
import shutil
import logging
import requests
from datetime import datetime

logger = logging.getLogger("NVR-Backup")

class BackupManager:
    def __init__(self, config, storage_path):
        self.config = config
        self.storage_path = storage_path
        self.last_backup_status = {
            "last_run": None,
            "status": "Never run",
            "backed_up_files": 0,
            "freed_or_copied_mb": 0,
            "message": ""
        }

    def run_backup(self):
        """Runs the configured backup operations (Telegram channel and/or secondary directory/NAS)."""
        backup_cfg = self.config.get("backup", {})
        if not backup_cfg.get("enabled", False):
            logger.info("Backup job triggered, but backup is not enabled in config.")
            return {
                "status": "skipped",
                "message": "Backup is disabled in configuration."
            }

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_copied = 0
        total_bytes = 0
        messages = []

        logger.info(f"Starting backup process at {now_str}...")

        # 1. Directory / NAS Backup
        target_dir = backup_cfg.get("target_path", "").strip()
        if target_dir:
            try:
                os.makedirs(target_dir, exist_ok=True)
                days_to_copy = backup_cfg.get("backup_recent_days", 1)
                cutoff_time = time.time() - (days_to_copy * 86400)

                for root, dirs, files in os.walk(self.storage_path):
                    for file in files:
                        if file.endswith(".mp4") or file.endswith(".jpg"):
                            src_file = os.path.join(root, file)
                            try:
                                if os.path.getmtime(src_file) >= cutoff_time:
                                    rel_path = os.path.relpath(src_file, self.storage_path)
                                    dest_file = os.path.join(target_dir, rel_path)
                                    os.makedirs(os.path.dirname(dest_file), exist_ok=True)

                                    if not os.path.exists(dest_file) or os.path.getsize(src_file) != os.path.getsize(dest_file):
                                        shutil.copy2(src_file, dest_file)
                                        total_copied += 1
                                        total_bytes += os.path.getsize(src_file)
                            except Exception as fe:
                                logger.error(f"Error copying file {src_file}: {fe}")

                mb_copied = round(total_bytes / (1024 * 1024), 2)
                messages.append(f"Directory Backup: {total_copied} files copied to {target_dir} ({mb_copied} MB)")
                logger.info(f"Directory backup completed: {total_copied} files, {mb_copied} MB.")
            except Exception as e:
                err = f"Directory backup failed: {e}"
                logger.error(err)
                messages.append(err)

        # 2. Telegram Alert Snapshots Cloud Backup
        tg_cfg = backup_cfg.get("telegram", {})
        if tg_cfg.get("enabled") and tg_cfg.get("bot_token") and tg_cfg.get("chat_id"):
            try:
                tg_uploaded = self._backup_snapshots_to_telegram(tg_cfg["bot_token"], tg_cfg["chat_id"])
                messages.append(f"Telegram Backup: {tg_uploaded} snapshots uploaded")
            except Exception as e:
                err = f"Telegram backup error: {e}"
                logger.error(err)
                messages.append(err)

        final_msg = " | ".join(messages) if messages else "No backup actions configured."
        self.last_backup_status = {
            "last_run": now_str,
            "status": "success" if total_copied > 0 or "uploaded" in final_msg else "completed",
            "backed_up_files": total_copied,
            "copied_mb": round(total_bytes / (1024 * 1024), 2),
            "message": final_msg
        }

        return self.last_backup_status

    def _backup_snapshots_to_telegram(self, bot_token, chat_id):
        """Uploads recent alert snapshots from today to a Telegram channel/chat."""
        today_str = datetime.now().strftime("%Y-%m-%d")
        uploaded_count = 0

        for root, dirs, files in os.walk(self.storage_path):
            if os.path.basename(root) == "alerts":
                cam_id = os.path.basename(os.path.dirname(root))
                for file in files:
                    if file.startswith(f"alert_{today_str}") and file.endswith(".jpg"):
                        filepath = os.path.join(root, file)
                        try:
                            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                            with open(filepath, "rb") as f:
                                payload = {
                                    "chat_id": chat_id,
                                    "caption": f"☁️ [NVR Cloud Backup] Alert Snapshot {file} ({cam_id})"
                                }
                                files_dict = {"photo": (file, f, "image/jpeg")}
                                resp = requests.post(url, data=payload, files=files_dict, timeout=15)
                                if resp.status_code == 200:
                                    uploaded_count += 1
                        except Exception as e:
                            logger.error(f"Error uploading snapshot {file} to Telegram: {e}")

        return uploaded_count
