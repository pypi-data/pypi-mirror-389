"""
Python logger settings.
Uses ENV variables to control the log level:
from simple_logging import make_logger
my_logger = make_logger("MY_KEY")
my_logger.debug4("message")
run with:
MY_KEY=4 python blabla.py

"""
from __future__ import annotations
import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from colorama import Fore, Back, Style

D2 = logging.DEBUG2 = logging.DEBUG - 1
D3 = logging.DEBUG3 = logging.DEBUG - 2
D4 = logging.DEBUG4 = logging.DEBUG - 3
logging.addLevelName(D2, "DGB2")
logging.addLevelName(D3, "DGB3")
logging.addLevelName(D4, "DGB4")

STR_LEVELS = ["DEBUG", "DEBUG2", "DEBUG3", "DEBUG4", "INFO", "WARNING", "ERROR", "CRITICAL"]
_PRE_LOGGEZ = "%(asctime)s %(levelname)s"
_PRE = "%(asctime)s %(name)s-%(levelname)s"

def _colorize(msg: str) -> str:
    _colors = {
        "cyan": Fore.CYAN,
        "magenta": Fore.MAGENTA,
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "back_red": Back.RED,
        "back_cyan": Back.CYAN,
    }
    def _get_next(msg: str, replacements: dict[str, str]) -> str:
        for replacement in replacements.keys():
            if msg[0: len(replacement)] == replacement:
                return replacement
        raise RuntimeError(f"Found no next color in {msg} out of {list(replacements)}")

    active_color = None
    new_message = []
    i = 0
    while i < len(msg):
        if msg[i] == "<":
            assert active_color is None or msg[i + 1] == "/", f"Use </color> before starting a new color: {msg}"
            _color = _get_next(msg[i + 2:], _colors) if active_color else _get_next(msg[i + 1:], _colors)
            assert active_color is None or _color == active_color, f"Active color: {active_color}. Got: {_color}"
            skip = len(_color) + 1 + (active_color is not None)
            assert msg[i + skip] == ">", f"Expected <color>(ch {i}), got: {msg}"
            new_message.append((_colors[_color] if active_color is None else Style.RESET_ALL))
            active_color = None if active_color is not None else _color
            i += skip + 1
        else:
            new_message.append(msg[i])
            i += 1
    return "".join(new_message)

def _get_default_formats(pre: str):
    return {
        "DEBUG": _colorize(f"<cyan>[{pre}]</cyan> %(message)s <yellow>(%(filename)s:%(funcName)s:%(lineno)d)</yellow>"),
        "DEBUG2": _colorize(f"<back_cyan>[{pre}]</back_cyan> %(message)s <yellow>(%(filename)s:%(funcName)s:%(lineno)d)</yellow>"),
        "DEBUG3": _colorize(f"<magenta>[{pre}]</magenta> %(message)s <yellow>(%(filename)s:%(funcName)s:%(lineno)d)</yellow>"),
        "DEBUG4": _colorize(f"<back_red>[{pre}]</back_red> %(message)s <yellow>(%(filename)s:%(funcName)s:%(lineno)d)</yellow>"),
        "INFO": _colorize(f"<green>[{pre}]</green> %(message)s <yellow>(%(filename)s:%(funcName)s:%(lineno)d)</yellow>"),
        "WARNING": _colorize(f"<yellow>[{pre}]</yellow> %(message)s <yellow>(%(filename)s:%(funcName)s:%(lineno)d)</yellow>"),
        "ERROR": _colorize(f"<red>[{pre}]</red> %(message)s <yellow>(%(filename)s:%(funcName)s:%(lineno)d)</yellow>"),
        "CRITICAL": _colorize(f"<back_red>[{pre}]</back_red> %(message)s <yellow>(%(filename)s:%(funcName)s:%(lineno)d)</yellow>"),
    }

class LoggezLogger(logging.Logger):
    """small interface-like class on top of the default logger for the extra methods"""
    def add_file_handler(self, path: str):
        """adds file handler"""
    def remove_file_handler(self):
        """Removes file handler"""
    def get_file_handler(self) -> logging.FileHandler:
        """Gets the file handler. Must be called after add_file_handler"""

class _FileHandler(logging.FileHandler):
    """same as filehandler but create the file on emit so we don't end up with empty files"""
    def emit(self, record):
        Path(self.baseFilename).parent.mkdir(exist_ok=True, parents=True)
        return super().emit(record)

def _add_file_handler(_logger: logging.Logger, path: str):
    if any(isinstance(handler, logging.FileHandler) for handler in _logger.handlers):
        _logger.debug2("File handler exists already. Removing and replacing.")
        _remove_file_handler(_logger)
    _logger.debug2(f"Adding file handler to this logger ({_logger.name}) to '{path}'")
    _logger.addHandler(logging.FileHandler(path))

def _remove_file_handler(_logger: logging.Logger):
    fh = [handler for handler in _logger.handlers if isinstance(handler, logging.FileHandler)]
    assert len(fh) == 1, _logger.handlers
    _logger.debug2(f"Removing FileHandler: {fh[0]}")
    _logger.removeHandler(fh[0])

def _get_file_handler(_logger: logging.LoggerAdapter) -> logging.FileHandler:
    fh = [handler for handler in _logger.handlers if isinstance(handler, logging.FileHandler)]
    assert len(fh) == 1, _logger.handlers
    return fh[0]

class CustomFormatter(logging.Formatter):
    """Custom formatting for logger."""
    def __init__(self, formats, *args, **kwargs):
        self.formats = formats
        super().__init__(*args, **kwargs)

    def format(self, record):
        log_fmt = self.formats[record.levelno]
        formatter = logging.Formatter(log_fmt)
        formatter.formatTime = self.formatTime
        return formatter.format(record)

    # here we define the time format.
    def formatTime(self, record, datefmt=None):
        return super().formatTime(record, "%Y-%m-%dT%H:%M:%S")

def make_logger(key: str, exists_ok: bool=False, log_file: Path | str | None=None) -> LoggezLogger:
    ENV_KEY = f"{key}_LOGLEVEL"
    # defaults to -1 (no logger!).
    env_var = int(os.environ[ENV_KEY]) if ENV_KEY in os.environ else 0

    # we need numbers below 5 (last logging module used number)
    try:
        log_levels = {
            -1: logging.NOTSET,
            0: logging.INFO,
            1: logging.DEBUG,
            2: logging.DEBUG2,
            3: logging.DEBUG3,
            4: logging.DEBUG4,
        }
        loglvl = log_levels[env_var]
    except KeyError:
        sys.stderr.write(f"You tried to use {key}_LOGLEVEL={env_var}. You need to set it between -1 and 4\n")
        sys.exit(1)
    # add the custom ones in the logger

    if key in (X := logging.Logger.manager.loggerDict):
        if not exists_ok:
            raise ValueError(f"'{key}' exists in {list(X.keys())} already.\n")
        else:
            del logging.Logger.manager.loggerDict[key]


    # instantiate logger and set log level
    new_logger: logging.Logger = logging.getLogger(key)
    new_logger.setLevel(loglvl)
    new_logger.debug2 = lambda msg, *args: (new_logger._log(D2, msg, args=args) if loglvl > 0 and loglvl <= D2 else "")
    new_logger.debug3 = lambda msg, *args: (new_logger._log(D3, msg, args=args) if loglvl > 0 and loglvl <= D3 else "")
    new_logger.debug4 = lambda msg, *args: (new_logger._log(D4, msg, args=args) if loglvl > 0 and loglvl <= D4 else "")
    # add custom formatter to logger
    handler = logging.StreamHandler()

    # Example [TIME:LEVEL:NAME] Message [FILE:FUNC:LINE]. We can update some other format here easily
    default_formats = _get_default_formats(pre := (_PRE if key != "LOGGEZ" else _PRE_LOGGEZ))
    formats = {getattr(logging, k): os.getenv(f"{key}_{k}_MESSAGE", default_formats[k]) for k in STR_LEVELS}
    handler.setFormatter(CustomFormatter(formats))
    new_logger.addHandler(handler)
    new_logger.add_file_handler = lambda path: _add_file_handler(new_logger, path)
    new_logger.remove_file_handler = lambda: _remove_file_handler(new_logger)
    new_logger.get_file_handler = lambda: _get_file_handler(new_logger)

    if log_file is not None:
        file_handler = _FileHandler(log_file, mode="a", delay=True) # delay=True doesn't open the file yet.
        file_handler.setLevel(logging.INFO) # log everything to file if provided.
        file_default_format = (f"[{pre}] %(message)s (%(filename)s:%(funcName)s:%(lineno)d)")
        file_formats = {getattr(logging, k): file_default_format for k in STR_LEVELS}
        file_handler.setFormatter(CustomFormatter(file_formats))
        new_logger.addHandler(file_handler)

    return new_logger

loggez_logger = make_logger("LOGGEZ")
