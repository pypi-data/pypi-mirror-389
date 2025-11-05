# globallock

Distributed lock manager, support many types of backend, e.g. redis, django-redis, etcd, zookeeper...

## Install

```
pip install globallock
```

*Notice: there're two l in globallock.*

## RedisGlobalLock Usage

```python
from globallock import GlobalLockManager
from globallock import REDIS_GLOBAL_LOCK_CLASS
# RedisGlobalLock is the default engine class,
# so config item global_lock_engine_class is optional here
config = {
    "global_lock_engine_class": REDIS_GLOBAL_LOCK_CLASS, # optional
    "global_lock_engine_options": {
        # redis connection pool init options goes here...
        "host": "xxx",
        "port": 6379,
        "password": "xxx",
        "db": 0,
    }
}
lockman = GlobalLockManager(config)
lockname = "your unique lock name"
with lockman.lock(lockname, timeout=60, blocking=True, blocking_timeout=5) as lock:
    if lock.is_locked:
        pass # do something with lock...
    else:
        pass # do something without lock, mostly do NOTHING...

```

## DjangoRedisGlobalLock Usage


```python
from globallock import GlobalLockManager
from globallock import DJANGO_REDIS_GLOBAL_LOCK_CLASS
config = {
    "global_lock_engine_class": DJANGO_REDIS_GLOBAL_LOCK_CLASS, # required
    "global_lock_engine_options": {
        "redis-cache-name": "default", # redis-cache-name is default to `default`
    }
}
lockman = GlobalLockManager(config)
lockname = "your unique lock name"
with lockman.lock(lockname, timeout=60, blocking=True, blocking_timeout=5) as lock:
    if lock.is_locked:
        pass # do something with lock...
    else:
        pass # do something without lock, mostly do NOTHING...

```

## EtcdGlobalLock Usage

```python
from globallock import GlobalLockManager
from globallock import ETCD_GLOBAL_LOCK_CLASS
config = {
    "global_lock_engine_class": ETCD_GLOBAL_LOCK_CLASS, # required
    "global_lock_engine_options": { 
        # etcd3 client init options goes here...
    }
}
lockman = GlobalLockManager(config)
lockname = "your unique lock name"
with lockman.lock(lockname, timeout=60, blocking=True, blocking_timeout=5) as lock:
    if lock.is_locked:
        pass # do something with lock...
    else:
        pass # do something without lock, mostly do NOTHING...

```

## ZookeeperGlobalLock Usage

```python
from globallock import GlobalLockManager
from globallock import ZOOKEEPER_GLOBAL_LOCK_CLASS
config = {
    "global_lock_engine_class": ZOOKEEPER_GLOBAL_LOCK_CLASS, # required
    "global_lock_engine_options": { 
        # KazooClient init options goes here...
    }
}
lockman = GlobalLockManager(config)
lockname = "your unique lock name"
with lockman.lock(lockname, blocking=True, blocking_timeout=5) as lock:
    if lock.is_locked:
        pass # do something with lock...
    else:
        pass # do something without lock, mostly do NOTHING...

```
*Notice:*

- `timeout` parameter for `lockman.lock()` will not work for ZookeeperGlobalLock.
- With ZookeeperGlobalLock, if the process which ownned the lock kill without any signal(kill -9), other process can acquire the lock after a short time(about 10 seconds after the lock-owner process killed). With other global lock engine, you have to wait the lock's `timeout` effect, after the the lock-owner process killed.


## Engine Class Requirements

- RedisGlobalLock:
    * `pip install redis`
- DjangRedisGlobalLock: 
    * `pip install django-redis`
- EtcdGlobalLock:
    * You need to download the source code of etcd3 from `https://github.com/kragniz/python-etcd3`, and install it with shell command (`pip install .`). You can NOT install it via `pip install etcd3`. The latest version of etcd3 installed via pip is 0.12.0, but it can not work with it's requires packages of latest version.
    * Of course, if the `etcd3` package published in pypi upgraded, you can try to install it via pip command.
    * Before the `etcd3` projects goes on and release new package to fix the problems, you need another `etcd3` package instead.
- ZookeeperGlobalLock:
    * `pip install kazoo`

*Notice: The packages above are not added to the package's requirements.txt, so you need to install them by yourself, or put them into your projects' requirements.txt.*

## Test Passed With Pythons

- python36
- python37
- python38
- python39
- python310
- python311

## Releases

### v0.1.0

- First release.
- Add RedisGlobalLock implementations.
- Add DjangoRedisGlobalLock implementations.
- Add EtcdGlobalLock implementations.
- Add ZookeeperGlobalLock implementations.

### v0.1.1

- Doc update.

### v0.1.2

- GlobalLockManager.lock方法参数可以在初始化时设置。
- 添加globallock.django.get_default_global_lock_manager方法，允许在django中使用全局分布式锁。

### v0.1.3

- 修正globallock.django默认设置。

### v0.1.4

- Doc update.
