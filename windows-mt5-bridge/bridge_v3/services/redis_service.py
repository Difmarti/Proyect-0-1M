"""
Redis caching service
"""

import redis
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from bridge_v3.config import Settings
from bridge_v3.services.logger_service import LoggerService


logger = LoggerService.get_logger(__name__)


class RedisService:
    """Redis caching and pub/sub service"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None

    def connect(self) -> bool:
        """Connect to Redis"""
        try:
            self.client = redis.Redis(
                host=Settings.REDIS_HOST,
                port=Settings.REDIS_PORT,
                db=Settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            self.client.ping()
            logger.info(f"Connected to Redis at {Settings.REDIS_HOST}:{Settings.REDIS_PORT}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
            return False

    def close(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set a key-value pair with optional TTL (seconds)"""
        if not self.client:
            raise RuntimeError("Redis not connected")

        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            if ttl:
                self.client.setex(key, ttl, value)
            else:
                self.client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get a value by key"""
        if not self.client:
            raise RuntimeError("Redis not connected")

        try:
            value = self.client.get(key)
            if value is None:
                return None

            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None

    def hset(self, name: str, mapping: Dict[str, Any]) -> bool:
        """Set hash fields"""
        if not self.client:
            raise RuntimeError("Redis not connected")

        try:
            # Convert dict/list values to JSON strings
            processed_mapping = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    processed_mapping[key] = json.dumps(value)
                else:
                    processed_mapping[key] = str(value)

            self.client.hset(name, mapping=processed_mapping)
            return True
        except Exception as e:
            logger.error(f"Error setting hash {name}: {e}")
            return False

    def hget(self, name: str, key: str) -> Optional[Any]:
        """Get a hash field value"""
        if not self.client:
            raise RuntimeError("Redis not connected")

        try:
            value = self.client.hget(name, key)
            if value is None:
                return None

            # Try to parse as JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        except Exception as e:
            logger.error(f"Error getting hash field {name}:{key}: {e}")
            return None

    def hgetall(self, name: str) -> Optional[Dict[str, Any]]:
        """Get all hash fields"""
        if not self.client:
            raise RuntimeError("Redis not connected")

        try:
            result = self.client.hgetall(name)
            if not result:
                return None

            # Try to parse JSON values
            processed = {}
            for key, value in result.items():
                try:
                    processed[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    processed[key] = value

            return processed

        except Exception as e:
            logger.error(f"Error getting hash {name}: {e}")
            return None

    def delete(self, *keys: str) -> bool:
        """Delete one or more keys"""
        if not self.client:
            raise RuntimeError("Redis not connected")

        try:
            self.client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Error deleting keys: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            raise RuntimeError("Redis not connected")

        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key existence: {e}")
            return False

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter"""
        if not self.client:
            raise RuntimeError("Redis not connected")

        try:
            return self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {e}")
            return None

    def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement a counter"""
        if not self.client:
            raise RuntimeError("Redis not connected")

        try:
            return self.client.decr(key, amount)
        except Exception as e:
            logger.error(f"Error decrementing key {key}: {e}")
            return None

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key"""
        if not self.client:
            raise RuntimeError("Redis not connected")

        try:
            self.client.expire(key, seconds)
            return True
        except Exception as e:
            logger.error(f"Error setting expiration on {key}: {e}")
            return False

    def cache_account_metrics(self, metrics: Dict[str, Any], ttl: int = 60) -> bool:
        """Cache account metrics with TTL"""
        return self.hset('account:metrics', metrics)

    def get_cached_account_metrics(self) -> Optional[Dict[str, Any]]:
        """Get cached account metrics"""
        return self.hgetall('account:metrics')

    def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            return self.client.ping() if self.client else False
        except Exception:
            return False

    def flush_cache(self, pattern: str = None) -> bool:
        """Flush cache by pattern or all"""
        if not self.client:
            raise RuntimeError("Redis not connected")

        try:
            if pattern:
                keys = self.client.keys(pattern)
                if keys:
                    self.client.delete(*keys)
            else:
                self.client.flushdb()
            logger.info(f"Flushed cache (pattern: {pattern or 'all'})")
            return True
        except Exception as e:
            logger.error(f"Error flushing cache: {e}")
            return False
