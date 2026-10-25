
from flask import Flask, request, jsonify
from datetime import datetime
import socket

app = Flask(__name__)


@app.route("/time", methods=["GET"])
def get_time():
    return jsonify({
        "server_time": str(datetime.now()),
        "served_by": socket.gethostname()
    }), 200


@app.route("/echo", methods=["POST"])
def echo():
    data = request.get_json(silent=True)

    if not data or "message" not in data:
        return jsonify({
            "error": "field 'message' is required"
        }), 400

    return jsonify({
        "message": data["message"]
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
