import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # AWS
    AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL") or None
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")

    # Cache
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_TTL_SECONDS = int(os.getenv("REDIS_TTL_SECONDS", "2592000"))

    # Queues
    TEXT_QUEUE_NAME = os.getenv("TEXT_QUEUE_NAME", "moderation-text-queue")
    IMAGE_QUEUE_NAME = os.getenv("IMAGE_QUEUE_NAME", "moderation-image-queue")

    # Storage
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "moderation-images")

    # Model
    MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

    # Webhook
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")


config = Config()