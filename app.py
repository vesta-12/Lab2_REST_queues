"""HTTP boundary; processing is deliberately delegated to worker.py."""
import os
from pathlib import Path
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from queue_storage import QueueStorage, now, valid_message


def create_app(data_dir=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 32768
    app.config['QUEUE_ROOT'] = data_dir or os.environ.get(
        'LAB2_DATA_DIR', str(Path(__file__).parent / 'data'))

    def storage():
        return QueueStorage(app.config['QUEUE_ROOT'])

    def message():
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or set(body) != {'message'}:
            return None, (jsonify(error='body must be a JSON object containing only message'), 400)
        if not valid_message(body['message']):
            return None, (jsonify(error='message must be a non-blank string of 1..4096 characters'), 400)
        return body['message'], None

    @app.get('/time')
    def get_time():
        return jsonify(server_time=now())

    @app.post('/echo')
    def echo():
        text, error = message()
        return error if error else jsonify(message=text)

    @app.post('/jobs')
    def submit():
        text, error = message()
        if error:
            return error
        record = storage().submit(text)
        return jsonify(job_id=record['job_id'], status='queued'), 202

    @app.get('/jobs/<job_id>')
    def get_job(job_id):
        record = storage().get(job_id)
        return (jsonify(record), 200) if record else (jsonify(error='job not found'), 404)

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.errorhandler(OSError)
    @app.errorhandler(ValueError)
    def storage_error(error):
        app.logger.error('Storage unavailable: %s', type(error).__name__)
        return jsonify(error='storage temporarily unavailable'), 503

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=int(os.environ.get('PORT', '5001')))
