import tkinter as tk
from GameManager import GameManager


def center_window(window, width, height):
    """
    Center a tkinter window on the screen
    """
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

def main():
    root = tk.Tk()
    root.title("WordleTrack")
    center_window(root, 800, 700)

    game = GameManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
