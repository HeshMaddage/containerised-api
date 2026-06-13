import redis
import os

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

CACHE_TTL = 60  # seconds

def get_cached(key: str):
    return redis_client.get(key)

def set_cache(key: str, value: str):
    redis_client.setex(key, CACHE_TTL, value)

def invalidate_cache(pattern: str):
    for key in redis_client.scan_iter(pattern):
        redis_client.delete(key)