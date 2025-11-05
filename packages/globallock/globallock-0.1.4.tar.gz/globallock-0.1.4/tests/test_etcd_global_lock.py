"""关于EtcdGlobalLock的单元测试。
"""
import time
from unittest import TestCase

from globallock.base import GlobalLockManager
import test_etcd_global_lock_local_settings


class TestEtcdGlobalLock(TestCase):
    """EtcdGlobalLock测试用例。"""

    def test1(self):
        """测试EtcdGlobalLock是否可用。"""
        lockman = GlobalLockManager(test_etcd_global_lock_local_settings.config)
        lockname = "test test test"
        with lockman.lock(
            lockname,
            timeout=5,
            blocking_timeout=1,
        ) as lock:
            if lock.is_locked:
                assert True
            else:
                assert False

    def test2(self):
        """测试timeout的有效性。"""
        lockman = GlobalLockManager(test_etcd_global_lock_local_settings.config)
        lockname = "test/test/test"
        lock = lockman.lock(
            lockname,
            timeout=1,
            blocking_timeout=1,
        )
        assert lock.acquire()
        assert lock.acquire() is False
        time.sleep(3)
        assert lock.acquire()  # etcd锁超时f起作用
        lock.release()
