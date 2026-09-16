import redis
from src.config import config

_client = None

def get_client():
    global _client
    if _client is None:
        _client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            decode_responses=True,
        )
    return _client

def get_flag(key: str):
    return get_client().get(key)

def set_flag(key: str, flag: str, ttl: int = None):
    ttl = ttl or config.REDIS_TTL_SECONDS
    get_client().setex(key, ttl, flag)

def ping():
    return get_client().ping()