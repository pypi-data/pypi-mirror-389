"""基于etcd实现的分布式锁定。
"""

import etcd3
from .base import GlobalLockImplementationBase


class EtcdGlobalLock(GlobalLockImplementationBase):
    """基于etcd实现的分布式锁定。"""

    def __init__(self, config, name, **options):
        super().__init__(config, name, **options)
        self.etcd_client = self.get_etcd3_client()
        self.lock = self.etcd_client.lock(
            self.lock_key,
            ttl=self.timeout,
        )

    @property
    def lock_key(self):
        """
        etcd3中Lock自带/locks/前缀。
        所以我们自己的前缀不能再以/开头。
        """
        lkey = self.config.global_lock_key_prefix.replace(":", "/") + self.name
        lkey = lkey.lstrip("/")
        return lkey

    def acquire(self) -> bool:
        """
        请求锁。返回锁定结果。

        @result: bool, True表示锁定成功，False表示锁定失败。
        """
        if self.blocking:
            blocking_timeout = self.blocking_timeout
        else:
            blocking_timeout = 0
        return self.lock.acquire(timeout=blocking_timeout)

    def get_etcd3_client(self):
        """
        根据配置，生成连接池。

        所有锁管理器均共享这个连接池。
        """
        return etcd3.client(**self.config.global_lock_engine_options)
