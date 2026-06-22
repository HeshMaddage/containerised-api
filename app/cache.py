import redis
import os

redis_host = os.getenv("REDIS_HOST", "localhost")
if not redis_host or not redis_host.strip():
    redis_host = "localhost"

redis_port_str = os.getenv("REDIS_PORT", "6379")
if not redis_port_str or not redis_port_str.strip():
    redis_port = 6379
else:
    try:
        redis_port = int(redis_port_str)
    except ValueError:
        redis_port = 6379

redis_password = os.getenv("REDIS_PASSWORD") or os.getenv("REDISPASSWORD")
if not redis_password or not redis_password.strip():
    redis_password = None

redis_client = redis.Redis(
    host=redis_host,
    port=redis_port,
    password=redis_password,
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