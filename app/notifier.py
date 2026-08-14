import json
import logging
import urllib.request
import urllib.parse
import threading

logger = logging.getLogger("NVR-Notifier")

def _send_telegram(token, chat_id, message):
    if not token or not chat_id:
        return False, "Token or Chat ID missing"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = response.read()
            logger.debug(f"Telegram notification sent: {res_data}")
            return True, "Sent"
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return False, str(e)

from datetime import datetime

def format_discord_embed(message):
    if isinstance(message, dict):
        return message
        
    # Convert HTML bold/italic to Markdown for Discord
    clean_msg = message.replace("<b>", "**").replace("</b>", "**")
    clean_msg = clean_msg.replace("<i>", "*").replace("</i>", "*")
    
    title = "ℹ️ [NVR Notification]"
    color = 3447003 # Default Cyan
    
    if "terputus/offline" in message or "offline" in message:
        title = "🚨 [NVR Alert] Kamera Offline"
        color = 16711680 # Red
    elif "terhubung kembali" in message or "online" in message:
        title = "✅ [NVR Alert] Kamera Online"
        color = 65280 # Green
    elif "Kapasitas penyimpanan" in message or "Storage" in message or "Warning" in message:
        title = "⚠️ [NVR Storage Alert] Disk Space Low"
        color = 16753920 # Orange
    elif "Test" in message or "uji coba" in message:
        title = "🔔 [NVR Test] Test Connection"
        color = 49151 # Light Blue
        
    # Strip emojis/headers that are redundant with the embed title
    for prefix in ["⚠️ ", "✅ ", "🚨 ", "🔔 ", "ℹ️ "]:
        if clean_msg.startswith(prefix):
            clean_msg = clean_msg[len(prefix):]
            
    headers_to_strip = [
        "**[NVR Alert]** ", "**[NVR Storage Warning]** ", "**[NVR Test]** ",
        "<b>[NVR Alert]</b> ", "<b>[NVR Storage Warning]</b> ", "<b>[NVR Test]</b> "
    ]
    for header in headers_to_strip:
        if clean_msg.startswith(header):
            clean_msg = clean_msg[len(header):]
            
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    return {
        "embeds": [{
            "title": title,
            "description": clean_msg,
            "color": color,
            "timestamp": timestamp,
            "footer": {
                "text": "NVR Sistem Monitoring"
            }
        }]
    }

def _send_discord(webhook_url, message):
    if not webhook_url:
        return False, "Webhook URL missing"
    
    try:
        payload_dict = format_discord_embed(message)
        payload = json.dumps(payload_dict).encode("utf-8")
    except Exception as e:
        logger.error(f"Failed to format Discord embed: {e}")
        payload = json.dumps({"content": message}).encode("utf-8")
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "NVR-Notifier-Agent"
    }
    
    try:
        req = urllib.request.Request(webhook_url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            logger.debug("Discord notification sent.")
            return True, "Sent"
    except Exception as e:
        logger.error(f"Failed to send Discord notification: {e}")
        return False, str(e)

def send_notification(config, message):
    """Sends a notification asynchronously to Discord and/or Telegram if enabled."""
    notif_config = config.get("notifications", {})
    
    # Telegram
    tg_config = notif_config.get("telegram", {})
    if tg_config.get("enabled"):
        token = tg_config.get("bot_token")
        chat_id = tg_config.get("chat_id")
        t = threading.Thread(target=_send_telegram, args=(token, chat_id, message), daemon=True)
        t.start()
        
    # Discord
    dc_config = notif_config.get("discord", {})
    if dc_config.get("enabled"):
        webhook_url = dc_config.get("webhook_url")
        t = threading.Thread(target=_send_discord, args=(webhook_url, message), daemon=True)
        t.start()

def test_notification(telegram_settings=None, discord_settings=None):
    """Test function to send a verification message immediately and return status/error."""
    results = {}
    
    if telegram_settings and telegram_settings.get("enabled"):
        token = telegram_settings.get("bot_token")
        chat_id = telegram_settings.get("chat_id")
        ok, err = _send_telegram(token, chat_id, "🔔 <b>[NVR Test]</b> Ini adalah pesan uji coba dari sistem NVR Anda.")
        if ok:
            results["telegram"] = {"status": "success"}
        else:
            results["telegram"] = {"status": "error", "message": err}
            
    if discord_settings and discord_settings.get("enabled"):
        webhook_url = discord_settings.get("webhook_url")
        ok, err = _send_discord(webhook_url, "🔔 **[NVR Test]** Ini adalah pesan uji coba dari sistem NVR Anda.")
        if ok:
            results["discord"] = {"status": "success"}
        else:
            results["discord"] = {"status": "error", "message": err}
            
    return results
