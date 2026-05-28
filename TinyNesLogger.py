import syslog


class TinyNesLogger:
    IS_DEBUG = True
    @staticmethod
    def dbg_write(msg: str) -> None:
        if TinyNesLogger.IS_DEBUG:
            print(msg)
    @staticmethod
    def log_msg(msg: str) -> None:
        if TinyNesLogger.IS_DEBUG:
            print(msg)
        syslog.syslog(syslog.LOG_WARNING, msg)
    @staticmethod
    def log_exception(inst:Exception)->None:
        TinyNesLogger.log_msg(str(inst))
