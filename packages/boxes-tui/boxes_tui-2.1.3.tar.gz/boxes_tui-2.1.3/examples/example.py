from curses import wrapper
from tui import TUI

# A simple example for boxes.py usage

def main(stdscr):

    # you can pass functions into the menu contents
    # here is one to quit the program
    def quit_app():
        tui.cleanup() # Dont worry; the curses wrapper will make shure nothing will break.
        quit()

    # Make a new Menu intance
    tui = TUI(stdscr) # Passing in stdsrc --> using wrapper; not passing it in --> not using wrapper

    # Make new menu instance
    main_menu = tui.Menu(tui.stdscr, [("Hello", tui.nothing), ("Example Page", tui.nothing), ("Quit", quit_app)])
    
    # set the key to anything. Its recomended do use ```None```
    key = None

    # Main loop
    while True:
        # tick the menu and pass in the keypress
        main_menu.tick(key)
        tui.stdscr.refresh()
        key = tui.stdscr.getch()  # Make shure to run getch() **after** ticking the menu

if __name__ == "__main__":
    wrapper(main) # Call using the curses wrapper for security when crashing
                  # Boxes.py also supports not using the wrapper, by just leaving the window in the TUI constructor empty; but that isnt recomended;
                  # it will leave your terminal in an unusable shape when crashing