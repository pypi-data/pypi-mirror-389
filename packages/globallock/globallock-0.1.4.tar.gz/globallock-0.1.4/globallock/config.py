"""配置类。
"""

from zenutils import dictutils
from .constants import DEFAULT_GLOBAL_LOCK_ENGINE_CLASS
from .constants import DEFAULT_GLOBAL_LOCK_ENGINE_OPTIONS
from .constants import DEFAULT_GLOBAL_LOCK_KEY_PREFIX


class Config(dictutils.Object):
    """配置类。

    @todo: 后续统一修改为支持服务端统一管理、客户端缓存、实时更新机制的配置管理。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setdefault(
            "global_lock_engine_class",
            DEFAULT_GLOBAL_LOCK_ENGINE_CLASS,
        )
        self.setdefault(
            "global_lock_engine_options",
            DEFAULT_GLOBAL_LOCK_ENGINE_OPTIONS,
        )
        self.setdefault(
            "global_lock_key_prefix",
            DEFAULT_GLOBAL_LOCK_KEY_PREFIX,
        )
