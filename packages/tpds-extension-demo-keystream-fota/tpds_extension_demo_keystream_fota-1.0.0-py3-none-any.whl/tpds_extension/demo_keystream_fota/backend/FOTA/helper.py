# This file is governed by the terms outlined in the LICENSE file located in the root directory of
#  this repository. Please refer to the LICENSE file for comprehensive information.
import os
import re
import platform
from pydantic import BaseModel


class ResponseModel(BaseModel):
    status: bool = False
    message: str | None = None
    data: dict | None = None
    terminal_data: str | None = None


def get_mdb_path(mplab_path: str) -> str:
    mdb_file = "mdb.bat" if platform.system().lower() == "windows" else "mdb.sh"
    mdb_path = os.path.join(mplab_path, "mplab_platform", "bin", mdb_file)
    assert os.path.exists(mdb_path), "MDB script doesnt exist"
    return mdb_path


def remove_line_formating(line: str):
    # ANSI escape sequence pattern (matches color codes, cursor movements, etc.)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    control_chars = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
    line = ansi_escape.sub("", line)
    line = control_chars.sub("", line)
    return line.strip()
