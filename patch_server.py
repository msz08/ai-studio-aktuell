import sys

with open("legvan-tv-remote/scripts/remote_server.py", "r") as f:
    lines = f.readlines()

new_routes = """
@app.route('/api/tools/install', methods=['POST'])
def tools_install():
    if 'file' not in request.files:
        return jsonify({'ok': False, 'error': 'No file uploaded'}), 400
    f = request.files['file']
    import os
    tmp_path = f"/dev/shm/{f.filename}"
    f.save(tmp_path)
    with _lock:
        try:
            res = get_tv().install_apk(tmp_path)
            os.remove(tmp_path)
            return jsonify({'ok': True, 'msg': res})
        except Exception as e:
            if os.path.exists(tmp_path): os.remove(tmp_path)
            return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/tools/push', methods=['POST'])
def tools_push():
    if 'file' not in request.files:
        return jsonify({'ok': False, 'error': 'No file uploaded'}), 400
    f = request.files['file']
    import os
    tmp_path = f"/dev/shm/{f.filename}"
    f.save(tmp_path)
    with _lock:
        try:
            get_tv().push_file(tmp_path, f"/sdcard/Download/{f.filename}")
            os.remove(tmp_path)
            return jsonify({'ok': True, 'msg': f"Pushed to Downloads"})
        except Exception as e:
            if os.path.exists(tmp_path): os.remove(tmp_path)
            return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/tools/screenshot', methods=['GET'])
def tools_screenshot():
    with _lock:
        try:
            data = get_tv().take_screenshot()
            from flask import Response
            return Response(data, mimetype='image/png')
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/tools/reboot', methods=['POST'])
def tools_reboot():
    with _lock:
        try:
            get_tv().reboot()
            return jsonify({'ok': True})
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/tools/storage', methods=['GET'])
def tools_storage():
    with _lock:
        try:
            res = get_tv().get_storage()
            return jsonify({'ok': True, 'msg': res})
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/tools/clearcache', methods=['POST'])
def tools_clearcache():
    with _lock:
        try:
            res = get_tv().clear_cache()
            return jsonify({'ok': True, 'msg': res})
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/apps', methods=['GET'])
def get_apps():
    with _lock:
        try:
            apps = get_tv().get_installed_apps()
            return jsonify({'ok': True, 'apps': apps})
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500
"""

idx = 0
for i, l in enumerate(lines):
    if l.startswith("if __name__ == '__main__':"):
        idx = i
        break

lines.insert(idx, new_routes + "\n")

with open("legvan-tv-remote/scripts/remote_server.py", "w") as f:
    f.writelines(lines)
