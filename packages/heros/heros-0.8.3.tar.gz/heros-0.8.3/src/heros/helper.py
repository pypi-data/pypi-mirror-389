import re
import logging


def object_name_from_keyexpr(key_expr, ns_objects, realm, endpoint=".*"):
    return re.search(f"{ns_objects}/{realm}/(.*?)/{endpoint}", key_expr).groups()[0]


def full_classname(o):
    """
    Return the fully qualified class name of an object.

    Args:
        o: object

    Returns:
        fully qualified module and class name
    """
    cl = o.__class__
    mod = cl.__module__
    if mod == "__builtin__":
        return cl.__name__  # avoid outputs like '__builtin__.str'
    return ".".join([mod, cl.__name__])


##############################################################
# extend logging mechanism
SPAM = 5
setattr(logging, "SPAM", 5)
logging.addLevelName(levelName="SPAM", level=5)


class Logger(logging.Logger):
    def setLevel(self, level, globally=False):
        """Set logger level; optionally propagate to all existing loggers."""
        if isinstance(level, str):
            level = level.upper()
        try:
            level = int(level)
        except ValueError:
            pass
        super().setLevel(level)
        if globally:
            for name, logger in logging.root.manager.loggerDict.items():
                if isinstance(logger, logging.Logger):
                    logger.setLevel(level)

    def spam(self, msg, *args, **kwargs):
        """Log a SPAM-level message."""
        if self.isEnabledFor(SPAM):
            self.log(SPAM, msg, *args, **kwargs)


# logger factory
def get_logger(name: str = "heros") -> Logger:
    logging.setLoggerClass(Logger)
    # Set up console handler only once
    if not logging.getLogger().handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(fmt="%(asctime)-15s %(name)s [%(filename)s:%(lineno)d %(funcName)s]: %(message)s")
        )
        logging.getLogger().addHandler(console_handler)
        logging.getLogger().setLevel(logging.INFO)  # default to show SPAM messages
    return logging.getLogger(name)


log = get_logger("heros")
