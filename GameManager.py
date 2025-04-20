import tkinter as tk
import time
from tkinter import messagebox, ttk
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import Counter

from WordBank import WordBank
from HintSystem import HintSystem
from AnalyticsEngine import AnalyticsEngine
from Player import Player
from DataManager import DataManager


class GameManager:
    """Controls game flow and user interactions."""

    def __init__(self, root):
        self.header_frame = None
        self.grid_frame = None
        self.main_frame = None
        self.root = root
        self.root.title("WordleTrack")
        self.data_manager = DataManager()
        self.config = self.data_manager.load_config()

        # game parameters
        self.word_length = self.config['word_length']
        self.max_attempts = self.config['max_attempts']
        self.current_attempt = 0
        self.game_active = False
        self.start_time = None
        self.difficulty = self.config['difficulty']
        self.word_bank = WordBank()  # No filename parameter
        self.player = Player(name="Player1")  # Initialize with default name
        self.current_word = None
        self.hint_system = HintSystem()
        self.analytics = AnalyticsEngine()
        self.colors = self.config['colors']
        self.create_widgets()
        self.add_keyboard_bindings()
        self.start_game()

    @staticmethod
    def load_config():
        """Load configuration or use defaults"""
        with open('config.json', 'r') as f:
            return json.load(f)

    def load_player(self):
        """Load player data or create new player"""
        try:
            return self.data_manager.load_player()
        except:
            return Player()

    def create_widgets(self):
        """Create all the game widgets"""
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.header_frame = tk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        self.title_label = tk.Label(
            self.header_frame,
            text="WordleTrack",
            font=('Arial', 24, 'bold')
        )
        self.title_label.pack(side=tk.LEFT)

        # Settings button
        self.settings_button = tk.Button(
            self.header_frame,
            text="⚙️",
            font=('Arial', 16),
            command=self.show_settings
        )
        self.settings_button.pack(side=tk.RIGHT)
        self.grid_frame = tk.Frame(self.main_frame, padx=10, pady=10)
        self.grid_frame.pack()
        self.entry_boxes = []
        for row in range(self.max_attempts):
            row_boxes = []
            for col in range(self.word_length):
                entry = tk.Entry(
                    self.grid_frame,
                    width=2,
                    font=('Arial', 24, 'bold'),
                    justify='center',
                    bg=self.colors['default'],
                    fg=self.colors['text'],
                    relief='solid',
                    borderwidth=2
                )
                entry.grid(row=row, column=col, padx=5, pady=5)
                entry.bind('<Key>', lambda event, r=row, c=col: self.on_key_press(event, r, c))
                entry.bind('<BackSpace>', lambda event, r=row, c=col: self.on_backspace(event, r, c))
                row_boxes.append(entry)
            self.entry_boxes.append(row_boxes)

        # button
        button_frame = tk.Frame(self.main_frame, padx=10, pady=5)
        button_frame.pack(pady=10)
        self.submit_button = tk.Button(
            button_frame,
            text="Submit",
            font=('Arial', 14),
            command=self.process_guess
        )
        self.submit_button.pack(side=tk.LEFT, padx=5)
        self.new_game_button = tk.Button(
            button_frame,
            text="New Game",
            font=('Arial', 14),
            command=self.start_game
        )
        self.new_game_button.pack(side=tk.LEFT, padx=5)
        self.hint_button = tk.Button(
            button_frame,
            text="Get Hint",
            font=('Arial', 14),
            command=self.get_hint
        )
        self.hint_button.pack(side=tk.LEFT, padx=5)
        self.stats_button = tk.Button(
            button_frame,
            text="Stats",
            font=('Arial', 14),
            command=self.show_stats
        )
        self.stats_button.pack(side=tk.LEFT, padx=5)
        self.create_virtual_keyboard() # keyboard

        # status bar
        self.status_bar = tk.Label(
            self.main_frame,
            text="Ready to play!",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_virtual_keyboard(self):
        """Create an on-screen keyboard"""
        self.keyboard_frame = tk.Frame(self.main_frame)
        self.keyboard_frame.pack(pady=10)

        # keyboard layout
        keyboard_layout = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Enter', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '⌫']
        ]

        # buttons
        self.key_buttons = {}
        for row_idx, row_keys in enumerate(keyboard_layout):
            row_frame = tk.Frame(self.keyboard_frame)
            row_frame.pack(pady=2)
            for key in row_keys:
                if key in ('Enter', '⌫'):
                    width = 5
                else:
                    width = 2
                button = tk.Button(
                    row_frame,
                    text=key,
                    width=width,
                    height=1,
                    font=('Arial', 12),
                    command=lambda k=key: self.virtual_key_press(k)
                )
                button.pack(side=tk.LEFT, padx=2)
                if key not in ('Enter', '⌫'):
                    self.key_buttons[key] = button

    def add_keyboard_bindings(self):
        """Add keyboard event bindings to the window"""
        self.root.bind('<Return>', lambda event: self.process_guess())
        self.root.bind('<Tab>', lambda event: self.focus_next_box())

    def focus_next_box(self):
        """Focus on the next available entry box"""
        if not self.game_active:
            return "break"
        focused = self.root.focus_get()
        current_row = self.current_attempt
        current_col = -1
        for col, entry in enumerate(self.entry_boxes[current_row]):
            if entry == focused:
                current_col = col
                break
        if current_col < self.word_length - 1:  # move to next column
            self.entry_boxes[current_row][current_col + 1].focus_set()
        return "break"

    def virtual_key_press(self, key):
        """Handle virtual keyboard button presses"""
        if not self.game_active:
            return
        if key == 'Enter':
            self.process_guess()
        elif key == '⌫':
            focused = self.root.focus_get()
            if isinstance(focused, tk.Entry):
                focused.event_generate('<BackSpace>')
        else:
            focused = self.root.focus_get()
            if isinstance(focused, tk.Entry):
                focused.delete(0, tk.END)
                focused.insert(0, key)
                row = self.current_attempt
                # move to next box
                for col, entry in enumerate(self.entry_boxes[row]):
                    if entry == focused and col < self.word_length - 1:
                        self.entry_boxes[row][col + 1].focus_set()
                        break

    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("300x200")
        settings_window.transient(self.root)
        settings_window.grab_set()

        # word length setting
        word_length_frame = tk.Frame(settings_window)
        word_length_frame.pack(fill=tk.X, pady=5, padx=10)
        tk.Label(word_length_frame, text="Word Length:").pack(side=tk.LEFT)
        word_length_var = tk.IntVar(value=self.word_length)
        word_length_options = [4, 5]
        for option in word_length_options:
            rb = tk.Radiobutton(
                word_length_frame,
                text=str(option),
                variable=word_length_var,
                value=option
            )
            rb.pack(side=tk.LEFT, padx=5)

        # Difficulty setting
        difficulty_frame = tk.Frame(settings_window)
        difficulty_frame.pack(fill=tk.X, pady=5, padx=10)
        tk.Label(difficulty_frame, text="Difficulty:").pack(side=tk.LEFT)
        difficulty_var = tk.StringVar(value=self.difficulty)
        difficulty_options = ['easy', 'medium', 'hard']

        for option in difficulty_options:
            rb = tk.Radiobutton(
                difficulty_frame,
                text=option.capitalize(),
                variable=difficulty_var,
                value=option
            )
            rb.pack(side=tk.LEFT, padx=5)

        apply_button = tk.Button(
            settings_window,
            text="Apply",
            command=lambda: self.apply_settings(word_length_var.get(), difficulty_var.get(), settings_window)
        )
        apply_button.pack(pady=20)

    def apply_settings(self, word_length, difficulty, settings_window):
        """Apply new settings and restart game"""
        self.word_length = word_length
        self.difficulty = difficulty
        self.config['word_length'] = word_length
        self.config['difficulty'] = difficulty
        with open('config.json', 'w') as f:
            json.dump(self.config, f)
        settings_window.destroy()
        # restart game with new settings
        self.recreate_game_grid()
        self.start_game()

    def recreate_game_grid(self):
        """Recreate the game grid with new word length"""
        # clear old grid
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        # create new entry boxes grid
        self.entry_boxes = []
        for row in range(self.max_attempts):
            row_boxes = []
            for col in range(self.word_length):
                entry = tk.Entry(
                    self.grid_frame,
                    width=2,
                    font=('Arial', 24, 'bold'),
                    justify='center',
                    bg=self.colors['default'],
                    fg=self.colors['text'],
                    relief='solid',
                    borderwidth=2
                )
                entry.grid(row=row, column=col, padx=5, pady=5)
                entry.bind('<Key>', lambda event, r=row, c=col: self.on_key_press(event, r, c))
                entry.bind('<BackSpace>', lambda event, r=row, c=col: self.on_backspace(event, r, c))
                row_boxes.append(entry)
            self.entry_boxes.append(row_boxes)

    def start_game(self):
        """Start a new game"""
        self.current_word = self.word_bank.get_random_word(self.difficulty, self.word_length)
        self.current_attempt = 0
        self.game_active = True
        self.start_time = time.time()
        print(f"New game started! Secret word: {self.current_word}")
        self.status_bar.config(text=f"New game started! Difficulty: {self.difficulty.capitalize()}")

        # reset hint
        self.hint_system.set_current_word(self.current_word)

        # reset keyboard
        for key, button in self.key_buttons.items():
            button.config(bg=self.colors['default'], fg=self.colors['text'])

        # clear all boxes and colors
        for row in range(self.max_attempts):
            for col in range(min(self.word_length, len(self.entry_boxes[row]))):
                self.entry_boxes[row][col].config(
                    state='normal',
                    bg=self.colors['default'],
                    readonlybackground=self.colors['default'],
                    disabledbackground=self.colors['default'],
                    fg=self.colors['text']
                )
                self.entry_boxes[row][col].delete(0, tk.END)
        self.entry_boxes[0][0].focus_set()

    def on_key_press(self, event, row, col):
        """Handle key presses in entry boxes"""
        if not self.game_active or row != self.current_attempt:
            return "break"
        if event.char.isalpha():
            self.entry_boxes[row][col].delete(0, tk.END)
            self.entry_boxes[row][col].insert(0, event.char.upper())
            if col < self.word_length - 1:
                self.entry_boxes[row][col + 1].focus_set()
            return "break"

    def on_backspace(self, event, row, col):
        """Handle backspace in entry boxes"""
        if not self.game_active or row != self.current_attempt:
            return "break"
        if not self.entry_boxes[row][col].get() and col > 0:
            self.entry_boxes[row][col - 1].focus_set()
            self.entry_boxes[row][col - 1].delete(0, tk.END)
            return "break"
        else:
            self.entry_boxes[row][col].delete(0, tk.END)
            return "break"

    def process_guess(self):
        """Process the current guess"""
        if not self.game_active:
            return
        guess = []
        for col in range(self.word_length):
            letter = self.entry_boxes[self.current_attempt][col].get().lower()
            if not letter:
                messagebox.showwarning("Incomplete", "Please fill in all letters!")
                return
            guess.append(letter)
        guess_word = ''.join(guess)

        # check if the word is valid
        if not self.word_bank.validate_word(guess_word):
            messagebox.showwarning("Invalid Word", "That's not a valid word!")
            return

        feedback = self.calculate_feedback(guess_word)  # calculate feedback
        self.hint_system.record_attempt(guess_word, feedback)  # record the attempt in hint system
        # record letter feedback
        for i, (letter, status) in enumerate(zip(guess_word, feedback)):
            self.analytics.record_letter_feedback(letter, i, status)
        # record the guess
        self.analytics.record_guess(guess_word, self.difficulty)

        self.apply_colors(feedback)
        self.update_keyboard_colors(guess_word, feedback)

        # check win
        if guess_word == self.current_word:
            self.end_game(True)
            return
        self.current_attempt += 1
        if self.current_attempt >= self.max_attempts:
            self.end_game(False)
        else:
            self.entry_boxes[self.current_attempt][0].focus_set()

    def update_keyboard_colors(self, guess_word, feedback):
        """Update the virtual keyboard colors based on feedback"""
        for i, letter in enumerate(guess_word):
            letter = letter.upper()
            if letter in self.key_buttons:
                button = self.key_buttons[letter]

                # update when the current is more correct than previous
                current_bg = button.cget('bg')
                new_bg = self.colors[feedback[i]]
                if (current_bg == self.colors['default'] or
                        (current_bg == self.colors['absent'] and feedback[i] in ['present', 'correct']) or
                        (current_bg == self.colors['present'] and feedback[i] == 'correct')):
                    button.config(bg=new_bg, fg='white' if feedback[i] != 'default' else self.colors['text'])

    def calculate_feedback(self, guess_word):
        """Calculate feedback for each letter in the guess using optimized algorithm"""
        feedback = ['absent'] * len(guess_word)
        from collections import Counter
        target_letters = Counter(self.current_word)

        # correct letters
        for i, (guess_char, target_char) in enumerate(zip(guess_word, self.current_word)):
            if guess_char == target_char:
                feedback[i] = 'correct'
                target_letters[guess_char] -= 1

        # present letters
        for i, char in enumerate(guess_word):
            if feedback[i] != 'correct' and target_letters[char] > 0:
                feedback[i] = 'present'
                target_letters[char] -= 1
        return feedback

    def apply_colors(self, feedback):
        """Apply colors to the current row based on feedback"""
        for col in range(self.word_length):
            color_key = feedback[col]
            bg_color = self.colors[color_key]
            self.entry_boxes[self.current_attempt][col].config(
                bg=bg_color,
                readonlybackground=bg_color,  # For readonly state
                disabledbackground=bg_color,  # For disabled state
                fg='white' if color_key != 'default' else self.colors['text'],
                state='readonly'  # Use readonly instead of disabled to maintain color
            )
            self.root.update_idletasks()

    def end_game(self, success):
        """End the current game and save detailed records"""
        self.game_active = False
        time_taken = time.time() - self.start_time
        game_data = {
            "word": self.current_word,
            "attempts": self.current_attempt + 1,
            "success": success,
            "time_taken": time_taken,
            "hints_used": self.player.hints_used,
            "difficulty": self.difficulty,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.data_manager.save_player_data(self.player.name, game_data)
        self.analytics.record_game(
            word=self.current_word,
            attempts=self.current_attempt + 1,
            success=success,
            time_taken=time_taken,
            difficulty=self.difficulty
        )
        if success:
            message = f"You guessed the word: {self.current_word.upper()} in {self.current_attempt + 1} attempts!"
            messagebox.showinfo("Congratulations!", message)
            self.status_bar.config(text=f"Success! {message}")
        else:
            message = f"The word was: {self.current_word.upper()}"
            messagebox.showinfo("Game Over", message)
            self.status_bar.config(text=f"Game over. {message}")

        self.disable_all_boxes()
        play_again = messagebox.askyesno("Play Again?", "Would you like to play another round?")
        if play_again:
            self.start_game()

    def disable_all_boxes(self):
        """Disable all entry boxes when game is over"""
        for row in range(self.max_attempts):
            for col in range(min(self.word_length, len(self.entry_boxes[row]))):
                self.entry_boxes[row][col].config(state='disabled')

    def get_hint(self):
        """Provide a hint to the player"""
        if not self.game_active:
            messagebox.showinfo("Hint", "Start a new game first!")
            return
        # record hint usage
        self.player.use_hint()

        # get hint
        hint = self.hint_system.generate_hint()
        messagebox.showinfo("Hint", hint)
        self.status_bar.config(text=f"Hint: {hint}")

    def show_stats(self):
        """Show player statistics with enhanced visualization"""
        try:
            stats_window = tk.Toplevel(self.root)
            stats_window.title("Your Statistics")
            stats_window.geometry("800x600")
            stats_window.transient(self.root)
            report = self.analytics.generate_report()

            if isinstance(report, str):
                tk.Label(stats_window, text=report, font=('Arial', 16)).pack(pady=20)
                return

            basic_stats_frame = tk.Frame(stats_window)
            basic_stats_frame.pack(fill=tk.X, pady=10)

            stats_text = (
                f"Games played: {report['games_played']}\n"
                f"Games won: {report['games_won']}\n"
                f"Success rate: {report['success_rate']:.1f}%\n"
                f"Average attempts: {report['avg_attempts']:.1f}\n"
                f"Average time: {report['avg_time']:.1f} seconds"
            )

            tk.Label(basic_stats_frame, text=stats_text, font=('Arial', 12), justify=tk.LEFT).pack(padx=20)

            notebook = ttk.Notebook(stats_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Tab 1: Attempts Distribution
            attempts_tab = ttk.Frame(notebook)
            notebook.add(attempts_tab, text="Attempts Distribution")
            fig1 = plt.Figure(figsize=(6, 4), dpi=100)
            ax1 = fig1.add_subplot(111)
            attempt_counts = Counter(self.analytics.guess_attempts)
            attempts = list(range(1, self.max_attempts + 1))
            frequencies = [attempt_counts.get(a, 0) for a in attempts]
            ax1.bar(attempts, frequencies, color='skyblue')
            ax1.set_title('Distribution of Attempts per Game')
            ax1.set_xlabel('Number of Attempts')
            ax1.set_ylabel('Frequency')
            canvas1 = FigureCanvasTkAgg(fig1, attempts_tab)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Tab 2: Win/Loss Ratio
            winloss_tab = ttk.Frame(notebook)
            notebook.add(winloss_tab, text="Win/Loss Ratio")
            fig2 = plt.Figure(figsize=(6, 4), dpi=100)
            ax2 = fig2.add_subplot(111)
            labels = ['Wins', 'Losses']
            sizes = [report['games_won'], report['games_played'] - report['games_won']]
            colors = ['lightgreen', 'lightcoral']
            ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax2.axis('equal')  # Equal aspect ratio ensures the pie chart is circular
            ax2.set_title('Win/Loss Ratio')
            canvas2 = FigureCanvasTkAgg(fig2, winloss_tab)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except ImportError:
            report = self.analytics.generate_report()
            if isinstance(report, str):
                stats_text = report
            else:
                stats_text = (
                    f"Games played: {report['games_played']}\n"
                    f"Games won: {report['games_won']}\n"
                    f"Success rate: {report['success_rate']:.1f}%\n"
                    f"Average attempts: {report['avg_attempts']:.1f}\n"
                    f"Average time: {report['avg_time']:.1f} seconds"
                )

            messagebox.showinfo("Statistics", stats_text)
