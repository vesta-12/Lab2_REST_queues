# Lab 2 - Service Requirements Specification

## 1. Overview

This project implements two communication approaches:

1. A synchronous REST API with `/time` and `/echo` endpoints.
2. An asynchronous message queue with a REST-based broker, producer, and consumer.

The services are implemented in Python using Flask and exchange data in JSON format over HTTP.

## 2. REST API

### GET /time

- Method: `GET`
- URL: `http://127.0.0.1:5001/time`
- Request body: none
- Success response: `200 OK`

Example:

```json
{
  "server_time": "2026-10-09 15:47:55.598426"
}
```

The `server_time` field is a string containing the current server date and time.

### POST /echo

- Method: `POST`
- URL: `http://127.0.0.1:5001/echo`
- Content-Type: `application/json`

Example request:

```json
{
  "message": "hello"
}
```

Success response: `200 OK`

```json
{
  "message": "hello"
}
```

If the JSON body is missing or does not contain the `message` field, the service returns `400 Bad Request`:

```json
{
  "error": "field 'message' is required"
}
```

## 3. Message Queue Broker

The broker runs separately from the REST API and stores messages in queues identified by topic.

### POST /queue/<topic>

Adds a new message to the selected queue.

Example:

`POST http://127.0.0.1:6000/queue/orders`

```json
{
  "order_id": 1,
  "created_at": "2026-10-09 18:59:16"
}
```

Success response: `201 Created`

```json
{
  "status": "queued",
  "topic": "orders"
}
```

### GET /queue/<topic>

Retrieves and removes the oldest message from the selected queue.

Example:

`GET http://127.0.0.1:6000/queue/orders`

If a message exists, the broker returns `200 OK` with the message in JSON format. Messages are processed in FIFO order.

If the queue is empty, the broker returns `204 No Content`.

## 4. Constraints

- Protocol: HTTP.
- Data format: JSON.
- Environment: Python 3.9+, Flask, requests, localhost.
- REST API port: `5001`.
- Queue broker port: `6000`.
- Port `5001` is used because port `5000` was already occupied in the local macOS environment.
- REST requests should normally respond within 1 second on localhost.
- The producer sends approximately one message per second.
- The consumer simulates approximately 3 seconds of processing per message.
- The system is intended for one producer and one consumer during the laboratory demonstration.
- The broker stores messages only in memory, so queued messages are lost if `broker.py` is stopped or restarted.
- Authentication, authorization, HTTPS, and persistent storage are outside the scope of this laboratory.

## 5. Assumptions

1. The REST API, broker, producer, and consumer run on the same local machine.
2. Ports `5001` and `6000` are available.
3. Clients send JSON in the expected format.
4. The producer may continue sending messages even when the consumer is stopped.
5. The broker remains active while messages are waiting in the queue.
6. A small laboratory workload is expected, so an in-memory Python list is sufficient.
7. One consumer is used, and messages are processed in FIFO order.

These assumptions keep the implementation simple while demonstrating the difference between synchronous REST communication and asynchronous producer-consumer communication.
