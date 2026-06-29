import curses
try:
    raise curses.error
except curses.error as e:
    print(f"Is instance: {isinstance(e, curses.error)}")
