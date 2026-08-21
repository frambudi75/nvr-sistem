from flask import Flask, render_template, request, jsonify, Response, send_from_directory, session, redirect, url_for
from functools import wraps
import logging
import subprocess
import os
import time
import glob
import shutil
import psutil

logger = logging.getLogger("NVR-Web")

app = Flask(__name__)
app.secret_key = 'nvr-secret-key-change-in-prod'

nvr_manager = None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            # If it's an API request, return 401 instead of redirecting
            if request.path.startswith('/api/'):
                return jsonify({"status": "error", "message": "Unauthorized"}), 401
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or session.get('role') != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({"status": "error", "message": "Admin privileges required"}), 403
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Read credentials from config auth block or fallback
        auth_config = nvr_manager.config.get("auth", {})
        
        # Check Admin
        admin_user = auth_config.get("admin_user", nvr_manager.config.get("admin_user", "admin"))
        admin_pass = auth_config.get("admin_pass", nvr_manager.config.get("admin_pass", "admin"))
        
        # Check Viewer
        viewer_user = auth_config.get("viewer_user", "viewer")
        viewer_pass = auth_config.get("viewer_pass", "viewer")
        
        if username == admin_user and password == admin_pass:
            session['logged_in'] = True
            session['role'] = 'admin'
            return redirect(url_for('index'))
        elif username == viewer_user and password == viewer_pass:
            session['logged_in'] = True
            session['role'] = 'viewer'
            return redirect(url_for('index'))
        else:
            return render_template("login.html", error="Invalid credentials")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route("/")
@login_required
def index():
    user_role = session.get('role', 'viewer')
    return render_template("index.html", config=nvr_manager.config, role=user_role)

@app.route("/api/config", methods=["GET"])
@login_required
def get_config():
    return jsonify(nvr_manager.config)

@app.route("/api/config", methods=["POST"])
@admin_required
def update_config():
    try:
        new_config = request.json
        nvr_manager.config = new_config
        
        # Save to file
        if nvr_manager.save_config():
            # Reload engine with new config
            nvr_manager.reload_config()
            return jsonify({"status": "success", "message": "Configuration updated and applied"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to save configuration file"}), 500
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/test_camera", methods=["POST"])
@admin_required
def test_camera():
    rtsp_url = request.json.get("rtsp_url")
    if not rtsp_url:
        return jsonify({"status": "error", "message": "RTSP URL is required"}), 400
    
    logger.info(f"Testing RTSP connection: {rtsp_url}")
    command = [
        "ffprobe",
        "-rtsp_transport", "tcp",
        "-v", "error",
        "-show_format",
        "-i", rtsp_url
    ]
    
    try:
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        if process.returncode == 0:
            return jsonify({"status": "success", "message": "Connection successful!"}), 200
        else:
            err_msg = process.stderr.decode('utf-8').strip()
            return jsonify({"status": "error", "message": f"Connection failed: {err_msg}"}), 400
    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "message": "Connection timed out (10s)"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/status", methods=["GET"])
@login_required
def get_status():
    status = []
    cameras_config = {cam["id"]: cam for cam in nvr_manager.config.get("cameras", [])}
    
    for cam_id, cam in cameras_config.items():
        cam_status = {
            "id": cam_id,
            "name": cam.get("name"),
            "enabled": cam.get("enabled", True),
            "recording": False
        }
        if cam_id in nvr_manager.recorders:
            recorder = nvr_manager.recorders[cam_id]
            cam_status["recording"] = recorder.check_health()
        
        status.append(cam_status)
        
    return jsonify(status)

@app.route("/api/sysinfo", methods=["GET"])
@login_required
def get_sysinfo():
    try:
        total, used, free = shutil.disk_usage(nvr_manager.storage_path)
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        
        return jsonify({
            "storage_path": nvr_manager.storage_path,
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "percent_used": round((used / total) * 100, 1) if total > 0 else 0,
            "cpu_percent": cpu,
            "ram_percent": ram
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/system/restart", methods=["POST"])
@admin_required
def restart_engine():
    try:
        # Just reload config and sync cameras to soft-restart recording streams
        nvr_manager.reload_config()
        return jsonify({"status": "success", "message": "NVR Engine restarted successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/system/logs", methods=["GET"])
@login_required
def get_logs():
    try:
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'nvr.log')
        if not os.path.exists(log_path):
            return jsonify({"logs": ["Log file not found."]})
            
        # Noise patterns to filter out from display
        noise_patterns = ['werkzeug', 'BrokenPipeError', 'ssl.SSLError', 'UNEXPECTED_EOF', 'Broken pipe', '_sslobj']
        
        with open(log_path, 'r') as f:
            lines = f.readlines()
            logs = []
            for line in lines:
                stripped = line.strip()
                if stripped and not any(p in stripped for p in noise_patterns):
                    logs.append(stripped)
            logs = logs[-100:]
            
        return jsonify({"logs": logs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/users/change_password", methods=["POST"])
@admin_required
def change_password():
    try:
        data = request.json
        new_user = data.get("username")
        new_pass = data.get("password")
        
        if not new_user or not new_pass:
            return jsonify({"status": "error", "message": "Username and password required"}), 400
            
        nvr_manager.config["admin_user"] = new_user
        nvr_manager.config["admin_pass"] = new_pass
        
        if nvr_manager.save_config():
            return jsonify({"status": "success", "message": "Credentials updated"}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to save config"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/notifications/test", methods=["POST"])
@admin_required
def test_notifications_route():
    try:
        data = request.json
        telegram_settings = data.get("telegram")
        discord_settings = data.get("discord")
        
        from notifier import test_notification
        results = test_notification(telegram_settings, discord_settings)
        
        # Check if there are failures
        has_error = False
        for channel, res in results.items():
            if res.get("status") == "error":
                has_error = True
                
        if has_error:
            return jsonify({"status": "error", "results": results}), 400
        return jsonify({"status": "success", "results": results}), 200
    except Exception as e:
        logger.error(f"Error testing notification: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def generate_mjpeg_stream(rtsp_url):
    command = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-i", rtsp_url,
        "-vf", "scale=640:-1", 
        "-r", "10",
        "-f", "image2pipe",
        "-vcodec", "mjpeg",
        "-q:v", "5",
        "-"
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        while True:
            header = process.stdout.read(2)
            if not header: break
            if header != b'\xff\xd8': continue
            
            frame_data = bytearray(header)
            while True:
                byte = process.stdout.read(1)
                if not byte: break
                frame_data.extend(byte)
                if len(frame_data) >= 2 and frame_data[-2:] == b'\xff\xd9': break
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
    finally:
        process.kill()

@app.route("/api/ptz/<cam_id>/<direction>", methods=["POST"])
@login_required
def ptz_control(cam_id, direction):
    import urllib.request
    import urllib.error
    import base64
    
    cameras_config = {cam["id"]: cam for cam in nvr_manager.config.get("cameras", [])}
    if cam_id not in cameras_config:
        return jsonify({"status": "error", "message": "Camera not found"}), 404
        
    cam = cameras_config[cam_id]
    brand = cam.get("brand", "generic")
    
    if brand != "hikvision":
        return jsonify({"status": "error", "message": "PTZ currently only supported for Hikvision via ISAPI in this version."}), 400
        
    ip = cam.get("ip")
    user = cam.get("username")
    password = cam.get("password")
    
    if not ip or not user or not password:
        return jsonify({"status": "error", "message": "Camera IP, Username, or Password missing"}), 400
        
    # Map direction to ISAPI PTZ continuous move values (pan, tilt)
    # Range is -100 to 100.
    ptz_map = {
        "up": (0, 60),
        "down": (0, -60),
        "left": (-60, 0),
        "right": (60, 0),
        "stop": (0, 0)
    }
    
    if direction not in ptz_map:
        return jsonify({"status": "error", "message": "Invalid direction"}), 400
        
    pan, tilt = ptz_map[direction]
    
    xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<PTZData version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
<pan>{pan}</pan>
<tilt>{tilt}</tilt>
</PTZData>"""

    url = f"http://{ip}/ISAPI/PTZCtrl/channels/1/continuous"
    req = urllib.request.Request(url, data=xml_data.encode('utf-8'), method='PUT')
    
    auth_b64 = base64.b64encode(f"{user}:{password}".encode('utf-8')).decode('utf-8')
    req.add_header("Authorization", f"Basic {auth_b64}")
    req.add_header("Content-Type", "application/xml")
    
    try:
        response = urllib.request.urlopen(req, timeout=3)
        if response.getcode() == 200:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": f"HTTP {response.getcode()}"}), 500
    except urllib.error.HTTPError as e:
        # Hikvision may require Digest Auth, which is complex for urllib. 
        # But some allow Basic. If it fails, we just return error.
        return jsonify({"status": "error", "message": f"Auth or protocol error: {e.code}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/stream/<cam_id>")
@login_required
def stream_camera(cam_id):
    cameras_config = {cam["id"]: cam for cam in nvr_manager.config.get("cameras", [])}
    if cam_id not in cameras_config:
        return "Camera not found", 404
        
    rtsp_url = cameras_config[cam_id].get("rtsp_url")
    if not rtsp_url:
        return "RTSP URL missing", 404
        
    return Response(generate_mjpeg_stream(rtsp_url), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/api/recordings/<cam_id>")
@login_required
def list_recordings(cam_id):
    cam_dir = os.path.join(nvr_manager.storage_path, cam_id)
    if not os.path.exists(cam_dir):
        return jsonify([])
        
    files = glob.glob(os.path.join(cam_dir, "*.mp4"))
    files.sort(reverse=True)
    
    dates_map = {}
    for f in files:
        basename = os.path.basename(f)
        date_str = os.path.basename(os.path.dirname(f))
        
        # Fallback if it's not in a date folder
        if "-" not in date_str or len(date_str) != 10:
            try:
                date_str = basename.split('_')[0]
            except:
                continue
                
        try:
            time_str = basename.split('_')[1].replace('.mp4', '').replace('-', ':')
            
            if date_str not in dates_map:
                dates_map[date_str] = []
            
            # Subpath for URL
            if os.path.basename(os.path.dirname(f)) == date_str:
                subpath = f"{date_str}/{basename}"
            else:
                subpath = basename
            
            dates_map[date_str].append({
                "time": time_str,
                "filename": basename,
                "path": f"/recordings/{cam_id}/{subpath}"
            })
        except:
            continue
            
    result = []
    for date, times in dates_map.items():
        result.append({"date": date, "files": times})
        
    return jsonify(result)

@app.route("/api/system/storage_analytics", methods=["GET"])
@login_required
def get_storage_analytics():
    try:
        analytics = []
        cameras_config = {cam["id"]: cam for cam in nvr_manager.config.get("cameras", [])}
        
        if os.path.exists(nvr_manager.storage_path):
            for item in os.listdir(nvr_manager.storage_path):
                item_path = os.path.join(nvr_manager.storage_path, item)
                if os.path.isdir(item_path):
                    cam_id = item
                    cam_name = cameras_config.get(cam_id, {}).get("name", cam_id)
                    
                    total_size = 0
                    files_count = 0
                    for root, _, files in os.walk(item_path):
                        for file in files:
                            if file.endswith(".mp4"):
                                file_path = os.path.join(root, file)
                                try:
                                    total_size += os.path.getsize(file_path)
                                    files_count += 1
                                except:
                                    continue
                                    
                    size_gb = round(total_size / (1024**3), 3)
                    analytics.append({
                        "id": cam_id,
                        "name": cam_name,
                        "size_gb": size_gb,
                        "files_count": files_count
                    })
        return jsonify(analytics)
    except Exception as e:
        logger.error(f"Error computing storage analytics: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/storage/cleanup/run_auto", methods=["POST"])
@admin_required
def run_auto_cleanup():
    try:
        from cleanup import Cleaner
        retention_days = nvr_manager.config.get("retention_days", 7)
        
        # 1. Retention cleanup
        if retention_days > 0:
            cleaner = Cleaner(nvr_manager.storage_path, retention_days)
            cleaner.cleanup_old_files()

        # 2. Smart storage cleanup if under min_free_gb
        smart_config = nvr_manager.config.get("smart_cleanup", {})
        min_free_gb = smart_config.get("min_free_gb", 5)
        if min_free_gb > 0 and os.path.exists(nvr_manager.storage_path):
            total, used, free = shutil.disk_usage(nvr_manager.storage_path)
            free_gb = free / (1024**3)
            if free_gb < min_free_gb:
                mp4_files = []
                for root, dirs, files in os.walk(nvr_manager.storage_path):
                    for file in files:
                        if file.endswith(".mp4"):
                            fpath = os.path.join(root, file)
                            try:
                                mp4_files.append((fpath, os.path.getmtime(fpath), os.path.getsize(fpath)))
                            except Exception:
                                pass
                mp4_files.sort(key=lambda x: x[1])
                for fpath, mtime, sz in mp4_files:
                    try:
                        os.remove(fpath)
                        total, used, free = shutil.disk_usage(nvr_manager.storage_path)
                        if (free / (1024**3)) >= (min_free_gb + 2):
                            break
                    except Exception:
                        pass
                        
        return jsonify({
            "status": "success",
            "message": "Auto-cleanup triggered successfully."
        }), 200
    except Exception as e:
        logger.error(f"Error triggering auto cleanup: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/storage/cleanup/manual", methods=["POST"])
@admin_required
def manual_cleanup():
    try:
        data = request.json or {}
        days = data.get("days")
        cam_id = data.get("cam_id") # "all" or specific cam_id
        clear_alerts = data.get("clear_alerts", False)
        
        deleted_files = 0
        freed_bytes = 0
        
        target_dirs = []
        if cam_id and cam_id != "all":
            cam_path = os.path.join(nvr_manager.storage_path, cam_id)
            if os.path.exists(cam_path):
                target_dirs.append(cam_path)
        else:
            if os.path.exists(nvr_manager.storage_path):
                target_dirs = [os.path.join(nvr_manager.storage_path, d) for d in os.listdir(nvr_manager.storage_path) if os.path.isdir(os.path.join(nvr_manager.storage_path, d))]

        now = time.time()
        cutoff_time = (now - (float(days) * 86400)) if (days is not None and str(days) != "" and float(days) >= 0) else None

        for tdir in target_dirs:
            for root, dirs, files in os.walk(tdir, topdown=False):
                # If clear_alerts is True, delete files in alerts dir
                if clear_alerts and os.path.basename(root) == "alerts":
                    for file in files:
                        fpath = os.path.join(root, file)
                        try:
                            freed_bytes += os.path.getsize(fpath)
                            os.remove(fpath)
                            deleted_files += 1
                        except Exception:
                            pass
                            
                for file in files:
                    if file.endswith(".mp4"):
                        fpath = os.path.join(root, file)
                        try:
                            mtime = os.path.getmtime(fpath)
                            if cutoff_time is None or mtime < cutoff_time:
                                freed_bytes += os.path.getsize(fpath)
                                os.remove(fpath)
                                deleted_files += 1
                        except Exception:
                            pass

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        return jsonify({
            "status": "success",
            "deleted_files": deleted_files,
            "freed_mb": freed_mb,
            "message": f"Successfully deleted {deleted_files} files, freeing {freed_mb} MB."
        }), 200
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/recordings/<cam_id>/date/<date_str>", methods=["DELETE"])
@admin_required
def delete_date_recordings(cam_id, date_str):
    try:
        cam_dir = os.path.join(nvr_manager.storage_path, cam_id)
        if not os.path.exists(cam_dir):
            return jsonify({"status": "error", "message": "Camera directory not found"}), 404
            
        deleted_count = 0
        freed_bytes = 0
        
        for root, dirs, files in os.walk(cam_dir):
            for file in files:
                if file.endswith(".mp4") and file.startswith(date_str):
                    fpath = os.path.join(root, file)
                    try:
                        freed_bytes += os.path.getsize(fpath)
                        os.remove(fpath)
                        deleted_count += 1
                    except Exception:
                        pass
                        
        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        return jsonify({
            "status": "success",
            "deleted_files": deleted_count,
            "freed_mb": freed_mb,
            "message": f"Deleted {deleted_count} files for date {date_str} ({freed_mb} MB freed)."
        }), 200
    except Exception as e:
        logger.error(f"Error deleting date recordings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/recordings/<cam_id>/<path:filename>")
@login_required
def serve_recording(cam_id, filename):
    directory = os.path.join(nvr_manager.storage_path, cam_id)
    return send_from_directory(directory, filename, as_attachment=request.args.get('download') == '1')

@app.route("/api/playback/transcode/<cam_id>/<path:filename>")
@login_required
def transcode_playback(cam_id, filename):
    """
    Server-side FFmpeg transcoding proxy for H.264+/H.265 videos.
    Converts incompatible codec to standard H.264 baseline on-the-fly
    and streams the result to the browser as a playable MP4.
    """
    filepath = os.path.join(nvr_manager.storage_path, cam_id, filename)
    if not os.path.exists(filepath):
        return "File not found", 404

    def generate():
        command = [
            "ffmpeg",
            "-i", filepath,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-profile:v", "baseline",
            "-level", "3.1",
            "-pix_fmt", "yuv420p",
            "-an",  # skip audio (CCTV biasanya tidak punya audio)
            "-movflags", "frag_keyframe+empty_moov+faststart",
            "-f", "mp4",
            "-loglevel", "error",
            "pipe:1"
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            while True:
                chunk = process.stdout.read(65536)
                if not chunk:
                    break
                yield chunk
        finally:
            process.kill()
            process.wait()

    return Response(generate(), mimetype='video/mp4')

@app.route("/api/recordings/export_clip", methods=["POST"])
@login_required
def export_clip():
    import time
    import tempfile
    from flask import send_file
    
    try:
        data = request.json
        cam_id = data.get("cam_id")
        date = data.get("date")
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        
        time_lapse = data.get("time_lapse", False)
        
        if not all([cam_id, date, start_time, end_time]):
            return jsonify({"status": "error", "message": "Missing required fields (cam_id, date, start_time, end_time)"}), 400
            
        try:
            start_parts = [int(x) for x in start_time.split(':')]
            end_parts = [int(x) for x in end_time.split(':')]
            start_secs = start_parts[0] * 3600 + start_parts[1] * 60 + (start_parts[2] if len(start_parts) > 2 else 0)
            end_secs = end_parts[0] * 3600 + end_parts[1] * 60 + (end_parts[2] if len(end_parts) > 2 else 0)
        except Exception as e:
            return jsonify({"status": "error", "message": f"Invalid time format (HH:MM:SS): {e}"}), 400
            
        duration = end_secs - start_secs
        if duration <= 0:
            return jsonify({"status": "error", "message": "End time must be after start time"}), 400
        
        # Extended limit for time-lapse
        max_duration = 10800 if time_lapse else 1800
        if duration > max_duration:
            return jsonify({"status": "error", "message": f"Max clip duration is {int(max_duration/60)} minutes"}), 400
            
        cam_dir = os.path.join(nvr_manager.storage_path, cam_id)
        if not os.path.exists(cam_dir):
            return jsonify({"status": "error", "message": "Camera recordings directory not found"}), 404
            
        files = glob.glob(os.path.join(cam_dir, "*.mp4"))
        selected_file = None
        offset = 0
        
        for f in files:
            basename = os.path.basename(f)
            if not basename.startswith(date):
                continue
            try:
                time_part = basename.split('_')[1].replace('.mp4', '')
                time_parts = [int(x) for x in time_part.split('-')]
                file_start_secs = time_parts[0] * 3600 + time_parts[1] * 60 + time_parts[2]
                file_end_secs = file_start_secs + nvr_manager.segment_time
                
                if file_start_secs <= start_secs <= file_end_secs:
                    selected_file = f
                    offset = start_secs - file_start_secs
                    break
            except:
                continue
                
        if not selected_file:
            return jsonify({"status": "error", "message": "No recording file covers the start time on this date"}), 404
            
        temp_dir = tempfile.gettempdir()
        now = time.time()
        for f in glob.glob(os.path.join(temp_dir, "clip_*.mp4")):
            try:
                if now - os.path.getmtime(f) > 600:
                    os.remove(f)
            except:
                pass
                
        safe_start = start_time.replace(':', '-')
        safe_end = end_time.replace(':', '-')
        output_filename = f"clip_{cam_id}_{date}_{safe_start}_{safe_end}.mp4"
        temp_output_path = os.path.join(temp_dir, output_filename)
        
        if time_lapse:
            command = [
                "ffmpeg", "-y",
                "-ss", str(offset),
                "-t", str(duration),
                "-i", selected_file,
                "-filter:v", "setpts=0.05*PTS",
                "-an",
                "-loglevel", "error",
                temp_output_path
            ]
        else:
            command = [
                "ffmpeg", "-y",
                "-ss", str(offset),
                "-t", str(duration),
                "-i", selected_file,
                "-c", "copy",
                "-map", "0",
                "-loglevel", "error",
                temp_output_path
            ]
        
        logger.info(f"Exporting clip: {command}")
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.returncode != 0:
            err_msg = process.stderr.decode('utf-8').strip()
            return jsonify({"status": "error", "message": f"FFmpeg cutting failed: {err_msg}"}), 500
            
        if not os.path.exists(temp_output_path) or os.path.getsize(temp_output_path) == 0:
            return jsonify({"status": "error", "message": "Output clip is empty or was not created"}), 500
            
        return send_file(temp_output_path, as_attachment=True, download_name=output_filename, mimetype='video/mp4')
        
    except Exception as e:
        logger.error(f"Error exporting clip: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def check_and_generate_ssl_certs(cert_path, key_path):
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return True
    
    logger.info("SSL certificates not found. Attempting to generate self-signed certificates...")
    try:
        command = [
            "openssl", "req",
            "-x509",
            "-newkey", "rsa:4096",
            "-nodes",
            "-out", cert_path,
            "-keyout", key_path,
            "-days", "365",
            "-subj", "/CN=localhost"
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            logger.info(f"Self-signed SSL certificates successfully generated: {cert_path}, {key_path}")
            return True
        else:
            logger.error(f"OpenSSL failed to generate certificate. Return code: {result.returncode}. Error: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        logger.warning("openssl command not found in system PATH. Cannot generate SSL certificates.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while generating SSL certificates: {e}")
        return False

def start_web_server(manager_instance, port=5000):
    global nvr_manager
    nvr_manager = manager_instance
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    logger.info(f"Starting Web Dashboard on port {port} (HTTP)")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
