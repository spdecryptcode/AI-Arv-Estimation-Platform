import os
import redis.asyncio as aioredis

# simple async Redis client used by multiple services
# uses REDIS_URL environment variable or defaults to docker-compose service
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
client: aioredis.Redis = aioredis.from_url(redis_url, decode_responses=True)
