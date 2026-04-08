import redis
import logging
import threading
from typing import Optional

from config import config

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                password=config.REDIS_PASSWORD if config.REDIS_PASSWORD else None,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            self.cache_enabled = True
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory cache: {e}")
            self.cache_enabled = False
            self.memory_cache = {}
    
    def get(self, key: str) -> Optional[str]:
        try:
            if self.cache_enabled:
                return self.redis_client.get(key)
            else:
                return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: int = 3600):
        try:
            if self.cache_enabled:
                self.redis_client.setex(key, ttl, value)
            else:
                self.memory_cache[key] = value
                # Simple in-memory cache expiration handling
                threading.Timer(ttl, lambda: self.memory_cache.pop(key, None)).start()
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
    
    def delete(self, key: str):
        try:
            if self.cache_enabled:
                self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
        except Exception as e:
            logger.error(f"Cache delete failed: {e}")

cache_manager = CacheManager()