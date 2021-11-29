import os

from core import run
import logging
import loguru


class Logger(logging.Logger):
    _logger: "loguru.Logger"

    def __init__(self, name: str):
        import loguru
        self._logger = loguru.logger
        super().__init__(name)

    def _log(self, level, msg, *args, **kwargs):
        self._logger.log(__level=level, __message=msg, *args, **kwargs)


DEBUG = bool(int(os.environ.get('DEBUG', 1)))
os.environ.setdefault('DEBUG', str(int(DEBUG)))
logging.setLoggerClass(Logger)
if DEBUG and False:
    logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    run()
