import logging
import os


def get_logger(name):
    if name:
        name = deal_name(name)  # 假设deal_name是定义好的函数
    else:
        name = __name__
    logger = logging.getLogger(name)
    # 检查logger是否已有handlers，避免重复添加
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def deal_name(name: str):
    folder, filename = os.path.split(name)
    base_name = os.path.splitext(filename)[0]
    folder_name = os.path.basename(folder)
    # 组合结果
    if filename.endswith(".py"):
        return f"{folder_name}-{base_name}"
    return name
