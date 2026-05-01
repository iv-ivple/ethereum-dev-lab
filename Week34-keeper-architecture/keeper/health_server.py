# keeper/health_server.py
from flask import Flask, jsonify
import threading

app = Flask(__name__)
_status = {}

@app.route("/health")
def health():
    return jsonify(_status)

def start_health_server(status_ref: dict, port: int = 8080):
    _status.update(status_ref)
    threading.Thread(target=lambda: app.run(port=port), daemon=True).start()
