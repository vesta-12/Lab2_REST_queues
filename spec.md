# Lab 3 - Service Requirements Specification (Version 2)

**Course:** Distributed & Cloud Computing  
**Laboratory:** Docker and Kubernetes  
**Student:** Sofiya Serbina  
**Version:** 2.0 (updated from Laboratory Work 2)

## 1. Overview

Laboratory Work 2 implemented two communication approaches:

1. A synchronous REST API with `/time` and `/echo` endpoints.
2. An asynchronous message queue with a separate REST-based broker, producer, and consumer.

Laboratory Work 3 reuses the existing Flask REST API and deploys it as a Docker container, then as multiple Kubernetes pods. The API remains stateless, so separate instances can process requests independently. The `/time` response now identifies the container or pod that handled the request using the `served_by` field.

Only the REST API is included in the Docker image and Kubernetes deployment. The queue components from Lab 2 are **not deployed or tested** in this laboratory.

## 2. REST API (Version 2)

The API uses HTTP and returns JSON responses. Inside the container, Flask listens on `0.0.0.0:5000`. On the macOS host, Docker maps port `5001` to container port `5000`.

### GET /time

- **Method:** `GET`
- **Docker host URL:** `http://127.0.0.1:5001/time`
- **Kubernetes URL:** `<URL returned by minikube service my-api --url>/time`
- **Request body:** none
- **Success status:** `200 OK`

Example response:

```json
{
  "server_time": "2026-10-25 15:06:53.053678",
  "served_by": "6e7f69cd8125"
}
```

Response fields:

- `server_time` — the current server date and time, represented as a string.
- `served_by` — the hostname of the responding instance, obtained using Python's `socket.gethostname()`. It identifies a Docker container when run with Docker and a pod when run with Kubernetes.

The `served_by` field makes it possible to count responses from different pods and demonstrate request distribution through a Kubernetes Service.

### POST /echo

- **Method:** `POST`
- **Docker host URL:** `http://127.0.0.1:5001/echo`
- **Kubernetes URL:** `<URL returned by minikube service my-api --url>/echo`
- **Content-Type:** `application/json`

Example request:

```json
{
  "message": "hello"
}
```

**Success status:** `200 OK`

```json
{
  "message": "hello"
}
```

If the JSON body is missing or the `message` field is absent, the API returns **`400 Bad Request`**:

```json
{
  "error": "field 'message' is required"
}
```

The endpoint does not save requests or responses between calls.

## 3. Containerization and Deployment Requirements

### Docker

- The application code is stored in `app/app.py`.
- `app/requirements.txt` contains `flask`.
- The Dockerfile uses `python:3.12-slim` as its base image.
- The Dockerfile copies and installs dependencies before copying the application code, allowing Docker to reuse cached dependency layers.
- The image is built as `my-api:lab3`.
- Flask listens on `0.0.0.0` and container port `5000`.
- The Docker Compose service is named `api`, builds from `./app`, and maps host port `5001` to container port `5000`.

### Kubernetes

- A Deployment named `my-api` manages **3 replicas** under normal operation.
- All pods use the image `my-api:lab3`, loaded into Minikube.
- The pod labels and Deployment selector use `app: my-api`.
- A Service named `my-api`, of type `NodePort`, uses selector `app: my-api` and forwards Service port `80` to container port `5000`.
- The Service provides access to the pod replicas through one logical endpoint.
- Across **30 requests** to `/time`, the `served_by` field must identify at least **2 different pods**.
- If a pod is deleted, the Deployment should create a replacement to maintain the desired replica count.
- The API should remain accessible through the Service during pod replacement while other healthy replicas are available.
- Scaling to **5 replicas** and back to **3 replicas** must be demonstrated.

## 4. Constraints

- Protocol: HTTP; response format: JSON.
- Runtime: Python 3.12 and Flask in the container.
- The Docker container port is `5000`; the macOS host uses port `5001` because host port `5000` was previously occupied.
- The locally exposed Minikube Service URL and port are provided by `minikube service my-api --url` and may vary between runs.
- The API must not depend on local in-memory session state or on a particular pod to handle consecutive requests.
- Only the API is included in the container; the Lab 2 queue broker, producer, and consumer are out of scope.
- AWS resources, AWS credentials, and other secrets are not required and must not be included in the Docker image.
- Authentication, authorization, HTTPS, and persistent storage are outside the scope of this laboratory.

## 5. Assumptions

1. Docker Desktop, Minikube, and kubectl are installed and running on the local macOS machine.
2. The Docker image is available to the Minikube cluster before the Kubernetes Deployment starts.
3. Clients send correctly formatted JSON for successful `/echo` requests.
4. Each API replica can answer `/time` and `/echo` without shared application state.
5. The Kubernetes Service selects the API pods using matching labels.
6. Healthy replicas are available to handle requests while a deleted pod is being replaced.
7. The laboratory uses a small local workload for request distribution, self-healing, and scaling tests.

## 6. Lab 2 Message Queue (Previous Version - Not Deployed in Lab 3)

The earlier project also included a separate in-memory message queue broker on port `6000`, with one producer and one consumer. The queue functionality is retained as background information only and is **not part of the Lab 3 REST API container**.

### POST /queue/<topic>

Adds a message to a queue identified by its topic. Example: `POST http://127.0.0.1:6000/queue/orders`. A successful request returns `201 Created` with the queue status and topic.

### GET /queue/<topic>

Retrieves and removes the oldest message from the selected queue using FIFO order. It returns `200 OK` with the message if one exists, or `204 No Content` if the queue is empty.

In Lab 2, the producer sent approximately one message per second and the consumer took approximately three seconds to process a message. The broker stored messages only in memory, so restarting it could cause queued messages to be lost. These behaviors are not evaluated in Lab 3.
