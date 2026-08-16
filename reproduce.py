import curses
import sys
import os

try:
    curses.initscr()
    # This should fail in some environments
    curses.start_color()
    print("Start color success")
except Exception as e:
    print(f"Start color failed: {e}")
    # This is what UIManager does
    try:
        curses.endwin()
        print("Endwin success")
    except Exception as e2:
        print(f"Endwin failed: {e2}")
    # Now it tries to print the version
    print("Version 1.1.5")

