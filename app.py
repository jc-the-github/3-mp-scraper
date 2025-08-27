from flask import Flask, render_template, jsonify
import subprocess
import logging

app = Flask(__name__)
import logging
import sys # Import the sys module to access standard output

# --- Basic logger setup (as before) ---
log_formatter = logging.Formatter('%(asctime)s - %(message)s')
live_logger = logging.getLogger('live_logger')
live_logger.setLevel(logging.INFO)

# --- Handler 1: The File (for the web UI) ---
file_handler = logging.FileHandler('live_scraper.log')
file_handler.setFormatter(log_formatter)
live_logger.addHandler(file_handler)

# --- Handler 2: The Console (for journalctl debugging) ---
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_formatter)
live_logger.addHandler(stream_handler)


# --- Example Usage ---
# Now, any message sent with this logger goes to BOTH the file and the console.
live_logger.info("This message will appear in live_scraper.log AND in the systemd journal.")
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
    print('huh?')
    # logger.info("Here's some info")

    return jsonify(run_systemctl_command('start'))

@app.route('/stop', methods=['POST'])
def stop_scraper():
    print('stoi?')
    
    return jsonify(run_systemctl_command('stop'))

# This endpoint reads the last 15 lines of the log file
# @app.route('/logs')
# def get_logs():
#     # if not os.path.exists('live_scraper.log'):
#     #     return jsonify([])
#     with open('live_scraper.log', 'r') as f:
#         lines = f.readlines()
#         return jsonify([line.strip() for line in lines[-15:]])

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