import logging
import colorlog

# Loggerの作成
logger = colorlog.getLogger()
logger.setLevel(logging.DEBUG)

# ログハンドラの設定
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s[%(levelname)s] %(message)s'))

logger.addHandler(handler)

# ログ出力
logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")
