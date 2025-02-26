import redis
import json
from ..config import settings

class CacheService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url)

    async def get(self, key: str):
        result = self.redis_client.get(key)
        return json.loads(result) if result else None

    async def set(self, key: str, value: dict):
        self.redis_client.setex(
            key,
            settings.cache_ttl,
            json.dumps(value)
        )

cache_service = CacheService() 