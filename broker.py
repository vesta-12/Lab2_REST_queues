from flask import Flask, request, jsonify
from collections import defaultdict

app = Flask(__name__)

queues = defaultdict(list)


@app.route("/queue/<topic>", methods=["POST"])
def enqueue(topic):
    data = request.get_json(silent=True) or {}
    queues[topic].append(data)

    return jsonify({
        "status": "queued",
        "topic": topic
    }), 201


@app.route("/queue/<topic>", methods=["GET"])
def dequeue(topic):
    if not queues[topic]:
        return "", 204

    message = queues[topic].pop(0)
    return jsonify(message), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)