from flask import Flask, render_template, jsonify
import subprocess

app = Flask(__name__)

# The service name we will create in Phase 2
SERVICE_NAME = "scraper.service"

def run_systemctl_command(command):
    """A helper function to run systemctl commands and return output."""
    try:
        # We use 'sudo' because systemctl requires root privileges
        result = subprocess.run(
            ['sudo', 'systemctl', command, SERVICE_NAME],
            check=True,
            capture_output=True,
            text=True
        )
        return {"status": "success", "output": result.stdout.strip()}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "output": e.stderr.strip()}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_scraper():
    return jsonify(run_systemctl_command('start'))

@app.route('/stop', methods=['POST'])
def stop_scraper():
    return jsonify(run_systemctl_command('stop'))

@app.route('/status', methods=['GET'])
def scraper_status():
    # The 'is-active' command is a simple way to check if it's running
    status_result = run_systemctl_command('is-active')
    if "inactive" in status_result.get('output', ''):
         return jsonify({"status": "inactive"})
    elif "active" in status_result.get('output', ''):
         return jsonify({"status": "active"})
    else:
         return jsonify({"status": "unknown", "details": status_result.get('output')})


if __name__ == '__main__':
    # Binds to all network interfaces, making it accessible via the public IP
    app.run(host='0.0.0.0', port=5000)