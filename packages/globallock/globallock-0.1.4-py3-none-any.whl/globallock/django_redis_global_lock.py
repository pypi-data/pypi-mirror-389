"""基于django-redis实现的分布式锁定。
"""

from django_redis import get_redis_connection
from .redis_global_lock import RedisGlobalLock


class DjangoRedisGlobalLock(RedisGlobalLock):
    """
    基于django-redis实现的分布式锁定。
    底层使用redis提供的分布式锁实现。
    与RedisGlobalLock的区别主要在于redis连接的获取方式，
    所以只需要重载get_lock函数即可。
    """

    def get_lock(self):
        """获得锁对象。"""
        return self.get_redis_connection().lock(
            self.lock_key,
            timeout=self.timeout,
            sleep=self.sleep,
            blocking=self.blocking,
            blocking_timeout=self.blocking_timeout,
            **self.other_options
        )

    def get_redis_connection(self):
        """从django的cache配置中获取redis连接。"""
        return get_redis_connection(
            self.config.global_lock_engine_options.get("redis-cache-name", "default")
        )
