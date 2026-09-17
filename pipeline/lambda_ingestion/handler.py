import json
import os
import uuid
import boto3
import redis

# --- Config (env vars so we can change these without touching code) ---
REDIS_HOST = os.environ.get("REDIS_HOST", "host.docker.internal")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

LOCALSTACK_HOSTNAME = os.environ.get("LOCALSTACK_HOSTNAME", "localhost.localstack.cloud")
EDGE_PORT = os.environ.get("EDGE_PORT", "4566")
SQS_ENDPOINT_URL = os.environ.get("SQS_ENDPOINT_URL", f"http://{LOCALSTACK_HOSTNAME}:{EDGE_PORT}")

QUEUE_NAME = os.environ.get("QUEUE_NAME", "moderation-text-queue")
_queue_url_cache = None

def get_queue_url():
    global _queue_url_cache
    if _queue_url_cache is None:
        _queue_url_cache = sqs_client.get_queue_url(QueueName=QUEUE_NAME)["QueueUrl"]
    return _queue_url_cache

redis_client = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, socket_connect_timeout=3
)
sqs_client = boto3.client("sqs", endpoint_url=SQS_ENDPOINT_URL, region_name="us-east-1")


def lambda_handler(event, context):
    # API Gateway wraps the payload in a "body" string; direct test invokes may not
    raw_body = event.get("body", event)
    try:
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
    except (json.JSONDecodeError, TypeError):
        return _response(400, {"error": "Invalid JSON body"})

    content_type = body.get("type")
    content = body.get("content")

    if not content_type or not content:
        return _response(400, {"error": "Missing 'type' or 'content' field"})

    cache_key = content.strip().lower()

    try:
        cached_flag = redis_client.get(cache_key)
    except redis.exceptions.RedisError as e:
        print(f"Redis error, failing open to queue: {e}")
        cached_flag = None

    if cached_flag is not None:
        return _response(200, {"source": "cache", "content": content, "flag": cached_flag})

    message_id = str(uuid.uuid4())
    try:
        sqs_client.send_message(
            QueueUrl=get_queue_url(),
            MessageBody=json.dumps({"id": message_id, "type": content_type, "content": content}),
        )
    except Exception as e:
        print(f"SQS send_message failed: {e}")
        return _response(500, {"error": "Failed to queue message"})

    return _response(202, {"source": "queued", "id": message_id, "content": content, "status": "pending"})


def _response(status_code, body_dict):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body_dict),
    }