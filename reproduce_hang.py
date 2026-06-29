import curses
import time

def test_napms():
    curses.initscr()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.cbreak()
    curses.noecho()
    
    try:
        print("Starting napms(10)...")
        curses.napms(10)
        print("Done")
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt")
    finally:
        curses.endwin()

if __name__ == "__main__":
    test_napms()
