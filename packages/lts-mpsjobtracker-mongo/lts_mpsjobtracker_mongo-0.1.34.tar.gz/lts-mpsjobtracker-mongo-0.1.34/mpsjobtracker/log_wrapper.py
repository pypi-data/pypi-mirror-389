import os, logging

level_values = {level:getattr(logging, level) for level in ('NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL',)}

def log_level_factory(level):
    value = level_values[level]
    def this_level(self, message, *args, **kwargs):
        if not 'flush' in kwargs:
            kwargs['flush'] = True

        if self.log_level <= value:
            print(message, *args, **kwargs)

    return this_level

class LogWrapperMeta(type):
    def __init__(cls, name, parents, dct):
        for level in level_values:
            fn = log_level_factory(level)
            fn.__name__ = level
            fn.__doc__ = f"Log at {level}"
            setattr(cls, level.lower(), fn)

class LogWrapper(metaclass=LogWrapperMeta):
    def __init__(self):
        configured_log_level = os.getenv('APP_LOG_LEVEL', 'INFO')
        # set log level, default to info if configured wrong
        self.log_level = level_values.get(configured_log_level, level_values['INFO'])

        # Metaclass creates methods for all log levels, e.g. LogWrapper(message).debug, LogWrapper(message).info()
