"""基于redis实现的分布式锁定。
"""

import redis
from zenutils import cacheutils
from .base import GlobalLockImplementationBase


class RedisGlobalLock(GlobalLockImplementationBase):
    """基于redis实现的分布式锁定。"""

    def __init__(self, config, name, **options):
        super().__init__(config, name, **options)
        self.lock = self.get_lock()

    def acquire(self) -> bool:
        """请求锁。返回锁定结果。

        @result: bool, True表示锁定成功，False表示锁定失败。
        """
        return self.lock.acquire()

    def get_lock(self):
        """获得锁对象。"""
        return redis.Redis(connection_pool=self.get_redis_connection_pool()).lock(
            self.lock_key,
            timeout=self.timeout,
            sleep=self.sleep,
            blocking=self.blocking,
            blocking_timeout=self.blocking_timeout,
            **self.other_options
        )

    @cacheutils.simple_cache
    def get_redis_connection_pool(self):
        """根据配置，生成连接池。

        所有锁管理器均共享这个连接池。
        """
        return redis.ConnectionPool(**self.config.global_lock_engine_options)
