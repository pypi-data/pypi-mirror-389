"""异常类集合。
"""


class GlobalLockClassNotFoundException(Exception):
    args = (210103001, "分布锁类未定义")
