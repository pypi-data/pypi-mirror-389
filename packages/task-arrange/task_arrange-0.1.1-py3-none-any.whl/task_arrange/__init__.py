from dotenv import load_dotenv, find_dotenv
dotenv_path = find_dotenv()
load_dotenv(".env", override=True)

from .log import Log
import logging
Log_ = Log(console_level = logging.WARNING, 
             log_file_name="app.log")
logger = Log_.logger
Log_.set_super_log(logger.critical)

super_log = Log_.super_log # 调试工具

def slog(s, target: str = "target",logger = logger.info):
    COLOR_RED = "\033[91m"
    COLOR_GREEN = "\033[92m"
    COLOR_YELLOW = "\033[93m"
    COLOR_BLUE = "\033[94m"
    COLOR_RESET = "\033[0m" # 重置颜色

    logger("\n"+f"{COLOR_GREEN}=={COLOR_RESET}" * 50)
    logger(target + "\n       "+"--" * 40)
    logger(type(s))
    logger(s)
    logger("\n"+f"{COLOR_GREEN}=={COLOR_RESET}" * 50)
