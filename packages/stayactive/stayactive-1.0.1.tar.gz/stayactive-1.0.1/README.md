# StayActive

A smart activity simulator utility that keeps your computer active while respecting your actual usage.

## Features

- **Smart Mouse Movement**: Randomly moves cursor within configurable pixel ranges
- **Periodic Key Presses**: Sends shift key presses at intervals to prevent sleep
- **User Activity Detection**: Automatically pauses when you're actually using your computer
- **Safety First**: Monitors real mouse/keyboard input and gets out of your way
- **Configurable**: Adjustable intervals, movement ranges, and activity timeouts

## Installation

```bash
pip install stayactive
```

## Usage

### Command Line
```bash
stayactive
```

### Python Module
```python
from stayactive import main
main()
```

## How It Works

StayActive runs in the background and:

1. **Moves your mouse cursor** slightly every 3 seconds
2. **Presses the shift key** every 60 seconds (20 × 3s intervals)
3. **Monitors your real activity** using mouse and keyboard listeners
4. **Pauses automatically** when you move the mouse, click, scroll, or type
5. **Resumes after 5 seconds** of inactivity

### Safety Features

- 🔴 **Auto-pause**: Detects real user input and pauses immediately
- 🟢 **Auto-resume**: Waits for inactivity before resuming automation
- 🛡️ **Non-intrusive**: Never interferes with your actual work

## Configuration

You can modify these constants in the source:

```python
MOVE_INTERVAL_SECONDS = 3      # How often to move mouse
MIN_PIXELS_TO_MOVE = 1         # Minimum movement distance
MAX_PIXELS_TO_MOVE = 15        # Maximum movement distance
KEY_PRESS_INTERVAL = 20        # Shift key every N mouse moves
USER_ACTIVITY_TIMEOUT = 5      # Seconds to wait after user stops
```

## Requirements

- Python 3.6+
- pyautogui
- pynput

## License

MIT License - see LICENSE file for details.

## Author

Rajdeep Banik (banik.rajdeep1056@gmail.com)
