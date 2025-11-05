"""分布锁管理。
"""

import logging
from zenutils import importutils
from .exceptions import GlobalLockClassNotFoundException
from .config import Config

_logger = logging.getLogger(__name__)


class GlobalLockImplementationBase:
    """锁实现基础类。"""

    def __init__(
        self, config, name, timeout, sleep, blocking, blocking_timeout, **other_options
    ):
        # create properties
        self.name = name
        self.timeout = timeout
        self.sleep = sleep
        self.blocking = blocking
        self.blocking_timeout = blocking_timeout
        self.other_options = other_options
        self.lock = None
        self._is_locked = False
        # load config items
        self.config = config

    @property
    def lock_key(self):
        """计算出锁在引擎中的key值。"""
        return self.config.global_lock_key_prefix + self.name

    @property
    def is_locked(self):
        """当前上下文是否已经获得锁。"""
        return self._is_locked

    def __enter__(self, *args, **kwargs):
        """进入锁定上下文。"""
        self._is_locked = self.acquire()
        return self

    def __exit__(self, *args, **kwargs):
        """离开锁定上下文。"""
        self.release()

    def acquire(self) -> bool:
        """请求锁。返回锁定结果。

        @result: bool, True表示锁定成功，False表示锁定失败。
        """
        raise NotImplementedError()

    def release(self):
        """释放锁。"""
        if self._is_locked and self.lock:
            try:
                self.lock.release()
            except Exception as error:  # pylint: disable=broad-exception-caught
                _logger.warning(
                    "release lock failed, mostly becuase of the main process takes more time than the lock's expire time or the lock engine connection failed: %s...",
                    error,
                )
            self._is_locked = False


class GlobalLockManager:
    """分布锁管理器。"""

    def __init__(self, config):
        self.config = Config(config or {})
        # pylint: disable=no-member
        self.lock_class = importutils.import_from_string(
            self.config.global_lock_engine_class
        )
        if self.lock_class is None:
            raise GlobalLockClassNotFoundException(
                f"global lock class {self.config.global_lock_engine_class} is NOT found..."
            )

    def lock(
        self,
        name,
        timeout=None,
        sleep=None,
        blocking=None,
        blocking_timeout=None,
    ) -> GlobalLockImplementationBase:
        """获取锁。使用with语法：

        ```
        with lockman.lock(lock_name, timeout=5, blocking=True, blocking_timeout=1) as lock:
            if lock.is_locked:
                pass # do something with lock
            else:
                pass # do something without lock, mostly does NOTHING
        ```
        """
        if timeout is None:
            timeout = self.config.get("timeout", None)
        if sleep is None:
            sleep = self.config.get("sleep", 0.1)
        if blocking is None:
            blocking = self.config.get("blocking", True)
        if blocking_timeout is None:
            blocking_timeout = self.config.get("blocking_timeout", None)
        return self.lock_class(
            self.config,
            name,
            timeout=timeout,
            sleep=sleep,
            blocking=blocking,
            blocking_timeout=blocking_timeout,
        )
