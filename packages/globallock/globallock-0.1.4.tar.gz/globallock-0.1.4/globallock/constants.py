"""常量及关联配置项。
"""

# 支持的分布式锁实现
REDIS_GLOBAL_LOCK_CLASS = "globallock.redis_global_lock.RedisGlobalLock"
DJANGO_REDIS_GLOBAL_LOCK_CLASS = (
    "globallock.django_redis_global_lock.DjangoRedisGlobalLock"
)
ETCD_GLOBAL_LOCK_CLASS = "globallock.etcd_global_lock.EtcdGlobalLock"
ZOOKEEPER_GLOBAL_LOCK_CLASS = "globallock.zookeeper_global_lock.ZookeeperGlobalLock"
# global_lock_engine_class
DEFAULT_GLOBAL_LOCK_ENGINE_CLASS = REDIS_GLOBAL_LOCK_CLASS
# global_lock_engine_options
DEFAULT_GLOBAL_LOCK_ENGINE_OPTIONS = {}
# global_lock_key_prefix
DEFAULT_GLOBAL_LOCK_KEY_PREFIX = "_glocks:"
