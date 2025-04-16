import tkinter as tk
from GameManager import GameManager


def main():
    root = tk.Tk()
    root.title("WordleTrack")
    root.geometry("800x700")  # Set initial window size

    game = GameManager(root)

    root.mainloop()


if __name__ == "__main__":
    main()