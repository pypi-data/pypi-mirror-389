"""基于redis实现的分布式锁定。
"""

from kazoo.client import KazooClient
from zenutils import cacheutils
from .base import GlobalLockImplementationBase


class ZookeeperGlobalLock(GlobalLockImplementationBase):
    """基于zookeeper实现的分布式锁定。"""

    def __init__(self, config, name, **options):
        super().__init__(config, name, **options)
        self.lock = self.get_lock()

    @property
    def lock_key(self):
        lkey = self.config.global_lock_key_prefix.replace(":", "/") + self.name
        if not lkey.startswith("/"):
            lkey = "/" + lkey
        return lkey

    def acquire(self) -> bool:
        """请求锁。返回锁定结果。

        @result: bool, True表示锁定成功，False表示锁定失败。
        """
        return self.lock.acquire(
            blocking=self.blocking,
            timeout=self.blocking_timeout,
        )

    def get_lock(self):
        """获得锁对象。"""
        return self.get_zk_client().Lock(self.lock_key)

    @cacheutils.simple_cache
    def get_zk_client(self):
        """根据配置，生成连接池。

        所有锁管理器均共享这个连接池。
        """
        zookeeper_client = KazooClient(**self.config.global_lock_engine_options)
        zookeeper_client.start()
        return zookeeper_client
