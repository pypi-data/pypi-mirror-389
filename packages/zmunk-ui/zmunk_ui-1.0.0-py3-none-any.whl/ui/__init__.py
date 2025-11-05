import os
import sys
import tty
import termios
from enum import Enum


def clear():
    os.system("clear")


def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


class Key(Enum):
    RIGHT = "right"
    LEFT = "left"
    UP = "up"
    DOWN = "down"
    ENTER = "enter"
    BACKSPACE = "backspace"
    EXIT = "exit"


def get_key() -> Key | str:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)

        if ch == "\x1b":  # ESC sequence
            ch += sys.stdin.read(2)
            match ch:
                case "\x1b[C":
                    return Key.RIGHT
                case "\x1b[D":
                    return Key.LEFT
                case "\x1b[A":
                    return Key.UP
                case "\x1b[B":
                    return Key.DOWN
                case _:
                    return ch

        if ch == "\x03":  # Ctrl+c
            return Key.EXIT
        elif ch == "\r" or ch == "\n":
            return Key.ENTER
        elif ch == "\x7f":
            return Key.BACKSPACE

        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
