from flask import Flask, render_template, request, jsonify, Response, send_from_directory, session, redirect, url_for
from functools import wraps
import logging
import subprocess
import os
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

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Read credentials from config or use default admin/admin
        valid_user = nvr_manager.config.get("admin_user", "admin")
        valid_pass = nvr_manager.config.get("admin_pass", "admin")
        
        if username == valid_user and password == valid_pass:
            session['logged_in'] = True
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
    return render_template("index.html", config=nvr_manager.config)

@app.route("/api/config", methods=["GET"])
@login_required
def get_config():
    return jsonify(nvr_manager.config)

@app.route("/api/config", methods=["POST"])
@login_required
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
@login_required
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
@login_required
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
            
        with open(log_path, 'r') as f:
            # Read last 100 lines
            lines = f.readlines()
            logs = [line.strip() for line in lines[-100:]]
            
        return jsonify({"logs": logs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/users/change_password", methods=["POST"])
@login_required
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
@login_required
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
        try:
            date_str = basename.split('_')[0]
            time_str = basename.split('_')[1].replace('.mp4', '').replace('-', ':')
            
            if date_str not in dates_map:
                dates_map[date_str] = []
            dates_map[date_str].append({
                "time": time_str,
                "filename": basename,
                "path": f"/recordings/{cam_id}/{basename}"
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

@app.route("/recordings/<cam_id>/<filename>")
@login_required
def serve_recording(cam_id, filename):
    directory = os.path.join(nvr_manager.storage_path, cam_id)
    return send_from_directory(directory, filename, as_attachment=request.args.get('download') == '1')

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
        if duration > 1800:
            return jsonify({"status": "error", "message": "Max clip duration is 30 minutes"}), 400
            
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
    
    app_dir = os.path.dirname(os.path.abspath(__file__))
    cert_path = os.path.join(app_dir, 'cert.pem')
    key_path = os.path.join(app_dir, 'key.pem')
    
    ssl_context = None
    if check_and_generate_ssl_certs(cert_path, key_path):
        ssl_context = (cert_path, key_path)
        logger.info(f"Starting Web Dashboard over HTTPS on port {port}")
    else:
        logger.warning(f"Falling back to HTTP. Starting Web Dashboard on port {port}")
        
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, ssl_context=ssl_context)
