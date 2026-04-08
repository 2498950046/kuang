# utils/cache_manager.py
import redis
import json
import hashlib
import re
from typing import List, Optional
import logging
from backendAdmin.config import Config
logger = logging.getLogger(__name__)


class CacheManager:
    def __init__(self, redis_url=Config.REDIS_URL):
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = 3600  # 1小时

    def get(self, key):
        """获取缓存"""
        try:
            value = self.redis_client.get(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return None

    def set(self, key, value, ttl=None):
        """设置缓存"""
        try:
            ttl = ttl or self.default_ttl
            self.redis_client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")

    def delete(self, key):
        """删除指定缓存"""
        try:
            return self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return 0

    def delete_pattern(self, pattern):
        """删除匹配模式的缓存"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"删除缓存模式 {pattern}: {len(keys)} 个键")
                return keys
            return []
        except Exception as e:
            logger.error(f"删除模式缓存失败 {pattern}: {e}")
            return []

    def clear_related_caches(self, mineral_name):
        """清除与矿物相关的所有缓存"""
        try:
            # 获取所有缓存键
            all_keys = self.redis_client.keys("*")

            related_keys = []
            for key in all_keys:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key

                # 检查是否是graph查询缓存
                if key_str.startswith("graph:"):
                    # 获取缓存值检查是否包含该矿物
                    value = self.get(key_str)
                    if value and mineral_name in value:
                        related_keys.append(key_str)

            if related_keys:
                self.redis_client.delete(*related_keys)
                logger.info(f"清除与矿物 '{mineral_name}' 相关的缓存: {len(related_keys)} 个")

            return related_keys
        except Exception as e:
            logger.error(f"清除相关缓存失败: {e}")
            return []

    def clear_all_graph_caches(self):
        """清除所有查询缓存"""
        try:
            self.redis_client.flushdb()
            logger.info("已清除所有Redis缓存")
            return True

        except Exception as e:
            logger.error(f"清除所有缓存失败: {e}")
            return False

    def invalidate_mineral_caches(self, mineral_name):
        """使矿物相关缓存失效（综合方法）"""
        # 1. 清除所有包含该矿物名的缓存
        patterns = [
            f"*{mineral_name}*",
            "graph:get_all_minerals*",
            "graph:*specimen*",
            f"search:*{mineral_name}*"
        ]

        total_deleted = 0
        for pattern in patterns:
            keys = self.delete_pattern(pattern)
            total_deleted += len(keys)

        return total_deleted


# 全局缓存管理器实例
cache_manager = CacheManager()