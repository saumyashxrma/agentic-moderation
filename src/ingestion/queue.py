import json
from src.aws_clients import get_sqs_client
from src.config import config

def get_queue_url(queue_name: str) -> str:
    sqs = get_sqs_client()
    return sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]

def enqueue_text(payload: dict):
    sqs = get_sqs_client()
    url = get_queue_url(config.TEXT_QUEUE_NAME)
    sqs.send_message(QueueUrl=url, MessageBody=json.dumps(payload))

def enqueue_image(payload: dict):
    sqs = get_sqs_client()
    url = get_queue_url(config.IMAGE_QUEUE_NAME)
    sqs.send_message(QueueUrl=url, MessageBody=json.dumps(payload))