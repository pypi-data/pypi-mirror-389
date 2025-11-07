import base64
import random
import string
import time
from typing import Generator
from warnings import warn


def chunk_list(input_list: list, n: int) -> Generator:
    """Yield successive n-sized chunks from `input_list`."""
    for i in range(0, len(input_list), n):
        yield input_list[i : i + n]


### ANCHOR: string modifier
def text_fill_center(input_text="example", fill="-", length=60):
    """Create a line with centered text."""
    text = f"{input_text}"
    return text.center(length, fill)


def text_fill_left(input_text="example", margin=15, fill_left="-", fill_right=" ", length=60):
    """Create a line with left-aligned text."""
    text = f"{(fill_left * margin)}{input_text}"
    return text.ljust(length, fill_right)


def text_fill_box(
    input_text: str = "", fill: str = " ", sp: str = "\u01c1", length: int = 60
) -> str:
    """
    Return a string centered in a box with side delimiters.

    Example:
        ```python
        text_fill_box("hello", fill="-", sp="|", length=20)
        '|-------hello-------|'
        ```

    Notes:
        - To input unicode characters, use the unicode escape sequence (e.g., "\u01c1" for a specific character). See [unicode-table]( https://symbl.cc/en/unicode-table) for more details.
            - ║ (Double vertical bar, `u2551`)
            - ‖ (Double vertical line, `u2016`)
            - ǁ (Latin letter lateral click, `u01C1`)
    """
    if len(sp) * 2 >= length:
        raise ValueError("Length must be greater than twice the side padding length")

    inner_width = length - 2 * len(sp)
    centered = input_text.center(inner_width, fill)
    return f"{sp}{centered}{sp}"


def text_repeat(input_str: str, length: int) -> str:
    """Repeat the input string to a specified length."""
    text = (input_str * ((length // len(input_str)) + 1))[:length]
    return text


def text_color(text: str, color: str = "blue") -> str:
    """ANSI escape codes for color the text.
    follow [this link](https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences) for more details.
    """
    ### Make color text with \033[<code>m
    ansi_code = {
        "red": "91",
        "green": "92",
        "yellow": "93",
        "blue": "94",
        "magenta": "95",
        "cyan": "96",
        "white": "97",
    }
    if color not in ansi_code:
        warn(f"Color '{color}' is not supported. Choose from {list(ansi_code.keys())}.")
        color = "white"

    text = "\033[" + ansi_code[color] + "m" + text + "\033[0m"
    return text


def time_uuid() -> str:
    timestamp = int(time.time() * 1.0e6)
    rand = random.getrandbits(10)
    unique_value = (timestamp << 10) | rand  # Combine timestamp + random bits
    text = base64.urlsafe_b64encode(unique_value.to_bytes(8, "big")).decode().rstrip("=")
    return text.replace("-", "_")


def simple_uuid():
    """Generate a simple random UUID of 4 digits."""
    rnd_letter = random.choice(string.ascii_uppercase)  # ascii_letters
    rnd_num = random.randint(100, 999)
    return f"{rnd_letter}{rnd_num}"
