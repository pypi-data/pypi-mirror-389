import copy
from django.conf import settings
from .base import GlobalLockManager
from .constants import DJANGO_REDIS_GLOBAL_LOCK_CLASS

# 从settings.py中获取全局分布式锁的设置
GLOBAL_LOCK_CONFIG = getattr(
    settings,
    "GLOBAL_LOCK_CONFIG",
    {},
)


def _get_config():
    config = copy.deepcopy(GLOBAL_LOCK_CONFIG)
    if not "global_lock_engine_class" in config:
        config["global_lock_engine_class"] = DJANGO_REDIS_GLOBAL_LOCK_CLASS
    if not "global_lock_engine_options" in config:
        config["global_lock_engine_options"] = {}
    if not "redis-cache-name" in config["global_lock_engine_options"]:
        config["global_lock_engine_options"]["redis-cache-name"] = "default"
    return config


def get_default_global_lock_manager():
    """根据Django settings.py的设置，获取分布式锁。"""
    config = _get_config()
    return GlobalLockManager(config)
