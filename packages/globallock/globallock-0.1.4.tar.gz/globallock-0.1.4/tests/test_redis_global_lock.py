"""关于RedisGlobalLock的单元测试。
"""
import uuid
from unittest import TestCase

from globallock.base import GlobalLockManager
from globallock.exceptions import GlobalLockClassNotFoundException
import test_redis_global_lock_local_settings


class TestRedisGlobalLock(TestCase):
    """关于RedisGlobalLock的单元测试。"""

    def test1(self):
        """测试RedisGlobalLock是否可用。"""
        lockman = GlobalLockManager(test_redis_global_lock_local_settings.config)
        lockname = str(uuid.uuid4())
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
        """测试RedisGlobalLock不可重入。"""
        lockman = GlobalLockManager(test_redis_global_lock_local_settings.config)
        lockname = str(uuid.uuid4())
        with lockman.lock(
            lockname,
            timeout=5,
            blocking=False,
        ) as lock:
            if lock.is_locked:
                assert True
                assert lock.acquire() is False
            else:
                assert False

    def test3(self):
        """测试实现类不存在的情况。"""
        config = {
            "global_lock_engine_class": "not_implemented_global_lock_class_path",
        }

        with self.assertRaises(GlobalLockClassNotFoundException):
            GlobalLockManager(config)
