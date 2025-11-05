[![PyPI]()](https://pypi.org/project/zmunk-ui/)

# Script utilities

Utility functions for interactive scripts.

## Installation

    python -m pip install zmunk-ui

## Examples

### Processing input
```python
from ui import hide_cursor, show_cursor, get_key, Key, clear

hide_cursor()

clear()

while True:
    key = get_key()
    clear()
    match key:
        case Key.RIGHT:
            print("move right")
        case Key.LEFT:
            print("move left")
        case c if isinstance(c, str):
            print("c:", c)
        case Key.EXIT:
            break


show_cursor()
```

### Printing colors
```python
from ui.colors import blue, red_bg

print(red_bg("Error"))
print(blue("Hello, world"))
```
