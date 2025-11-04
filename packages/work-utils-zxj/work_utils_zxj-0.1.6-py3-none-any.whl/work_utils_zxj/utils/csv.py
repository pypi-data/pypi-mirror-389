import re
from typing import Any
import pandas as pd
import os


def read_csv(file_path: str):
    if not file_path or not os.path.isfile(file_path):
        raise FileNotFoundError(f"Invalid file path: {file_path}")
    return pd.read_csv(file_path).to_dict(orient="records")


def write_csv(file_path: str, row: list[dict[str, Any]]):
    if not file_path:
        raise ValueError(f"file path can not be empty")
    if not row:
        return
    need_write_head = False
    if not os.path.exists(file_path):
        need_write_head = True
    pd.DataFrame(row).to_csv(file_path, index=False, mode="a", header=need_write_head)
