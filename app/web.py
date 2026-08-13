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

@app.route("/recordings/<cam_id>/<filename>")
@login_required
def serve_recording(cam_id, filename):
    directory = os.path.join(nvr_manager.storage_path, cam_id)
    return send_from_directory(directory, filename, as_attachment=request.args.get('download') == '1')

def start_web_server(manager_instance, port=5000):
    global nvr_manager
    nvr_manager = manager_instance
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    logger.info(f"Starting Web Dashboard on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
