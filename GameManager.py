import tkinter as tk
import time
from tkinter import messagebox, ttk
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from WordBank import WordBank
from HintSystem import HintSystem
from AnalyticsEngine import AnalyticsEngine
from Player import Player


class GameManager:
    """Controls game flow and user interactions."""

    def __init__(self, root):
        self.settings_button = None
        self.header_frame = None
        self.grid_frame = None
        self.main_frame = None
        self.root = root
        self.root.title("WordleTrack")
        self.config = self.load_config()

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
        """Load configuration from file"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {
                "word_length": 5,
                "max_attempts": 6,
                "difficulty": "medium",
                "colors": {
                    "correct": "#6aaa64",
                    "present": "#c9b458",
                    "absent": "#787c7e",
                    "default": "#ffff",
                    "text": "#0000"
                }
            }

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
        # self.data_manager.save_player_data(self.player.name, game_data)
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
        """Show player statistics with enhanced visualization based on CSV history data"""
        try:
            import pandas as pd
            import os
            import numpy as np
            from collections import Counter

            stats_window = tk.Toplevel(self.root)
            stats_window.title("Wordle Game Statistics")
            stats_window.geometry("900x700")
            stats_window.transient(self.root)

            # Path to the history file
            history_file = 'data/history/history_record.csv'

            if not os.path.exists(history_file):
                tk.Label(stats_window, text="No game history found.", font=('Arial', 16)).pack(pady=20)
                return

            # Read the CSV file
            df = pd.read_csv(history_file)

            # Generate basic statistics
            games_played = len(df)
            games_won = len(df[df['result'] == 'win'])
            success_rate = (games_won / games_played * 100) if games_played > 0 else 0
            avg_attempts = df['attempts'].mean() if not df.empty else 0
            avg_time = df['time_taken'].mean() if not df.empty else 0

            # Basic stats frame
            basic_stats_frame = tk.Frame(stats_window)
            basic_stats_frame.pack(fill=tk.X, pady=10)

            stats_text = (
                f"Games played: {games_played}\n"
                f"Games won: {games_won}\n"
                f"Success rate: {success_rate:.1f}%\n"
                f"Average attempts: {avg_attempts:.1f}\n"
                f"Average time: {avg_time:.1f} seconds"
            )

            tk.Label(basic_stats_frame, text="Game Statistics Summary", font=('Arial', 14, 'bold')).pack(pady=(10, 5))
            tk.Label(basic_stats_frame, text=stats_text, font=('Arial', 12), justify=tk.LEFT).pack(padx=20)

            notebook = ttk.Notebook(stats_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 1. Number of Attempts - Histogram
            attempts_tab = ttk.Frame(notebook)
            notebook.add(attempts_tab, text="Number of Attempts")
            fig1 = plt.Figure(figsize=(7, 5), dpi=100)
            ax1 = fig1.add_subplot(111)

            # Count frequency of each attempt number
            max_attempts = max(df['attempts'].max(), 6) if not df.empty else 6
            attempts_range = range(1, max_attempts + 1)
            attempts_data = df['attempts'].value_counts().reindex(attempts_range, fill_value=0)

            ax1.bar(attempts_data.index, attempts_data.values, color='skyblue', edgecolor='black')
            ax1.set_title('Distribution of Player Attempts per Game', fontsize=14)
            ax1.set_xlabel('Number of Attempts', fontsize=12)
            ax1.set_ylabel('Frequency', fontsize=12)
            ax1.set_xticks(attempts_range)
            ax1.grid(axis='y', linestyle='--', alpha=0.7)

            for i, v in zip(attempts_data.index, attempts_data.values):
                ax1.text(i, v + 0.1, str(v), ha='center')

            fig1.tight_layout()
            canvas1 = FigureCanvasTkAgg(fig1, attempts_tab)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 2. Success Rate (Win/Loss) - Pie Chart
            winloss_tab = ttk.Frame(notebook)
            notebook.add(winloss_tab, text="Success Rate (Win/Loss)")
            fig2 = plt.Figure(figsize=(7, 5), dpi=100)
            ax2 = fig2.add_subplot(111)

            results = Counter(df['result'])
            labels = list(results.keys())
            sizes = list(results.values())
            colors = ['lightgreen' if label == 'win' else 'lightcoral' for label in labels]

            ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, shadow=True)
            ax2.axis('equal')  # Equal aspect ratio ensures the pie chart is circular
            ax2.set_title('Proportion of Successful vs. Failed Games', fontsize=14)

            fig2.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, winloss_tab)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 3. Difficulty Level vs. Success Rate - Bar Graph
            difficulty_tab = ttk.Frame(notebook)
            notebook.add(difficulty_tab, text="Difficulty Level vs. Success Rate")
            fig3 = plt.Figure(figsize=(7, 5), dpi=100)
            ax3 = fig3.add_subplot(111)

            # Calculate success rate by difficulty
            difficulty_stats = df.groupby('difficulty').agg(
                games=('game_number', 'count'),
                wins=('result', lambda x: (x == 'win').sum())
            ).reset_index()
            difficulty_stats['success_rate'] = difficulty_stats['wins'] / difficulty_stats['games'] * 100

            # Ensure all difficulty levels are included with proper ordering
            difficulty_order = ['easy', 'medium', 'hard']
            difficulty_stats = difficulty_stats.set_index('difficulty').reindex(difficulty_order).reset_index()
            difficulty_stats = difficulty_stats.fillna(0)  # Fill NaN with 0 for difficulties with no data

            ax3.bar(difficulty_stats['difficulty'], difficulty_stats['success_rate'],
                    color=['#8BC34A', '#FFC107', '#F44336'])
            ax3.set_title('Success Rate by Difficulty Level', fontsize=14)
            ax3.set_xlabel('Difficulty Level', fontsize=12)
            ax3.set_ylabel('Success Rate (%)', fontsize=12)
            ax3.set_ylim(0, 100)  # Set y-axis from 0 to 100%
            ax3.grid(axis='y', linestyle='--', alpha=0.7)

            for i, v in enumerate(difficulty_stats['success_rate']):
                ax3.text(i, v + 1, f"{v:.1f}%", ha='center')

            fig3.tight_layout()
            canvas3 = FigureCanvasTkAgg(fig3, difficulty_tab)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 4. Hint Usage Frequency - Stacked Bar Graph
            # Note: We're assuming the CSV doesn't have hint usage data, so we'll simulate it
            # In a real implementation, you'd need to add hint usage data to your CSV
            hint_tab = ttk.Frame(notebook)
            notebook.add(hint_tab, text="Hint Usage Frequency")
            fig4 = plt.Figure(figsize=(7, 5), dpi=100)
            ax4 = fig4.add_subplot(111)

            # Sample hint usage data (simulated)
            # In a real implementation, replace this with actual data from your CSV
            difficulty_levels = ['easy', 'medium', 'hard']
            hint_types = ['Letter Hint', 'Word Hint', 'No Hint']

            # Create simulated data based on difficulty distribution in the real data
            difficulty_counts = df['difficulty'].value_counts().reindex(difficulty_levels, fill_value=0)

            # Create random hint usage with more hints for harder difficulties
            hint_data = {
                'easy': [difficulty_counts['easy'] * 0.2, difficulty_counts['easy'] * 0.1,
                         difficulty_counts['easy'] * 0.7],
                'medium': [difficulty_counts['medium'] * 0.3, difficulty_counts['medium'] * 0.2,
                           difficulty_counts['medium'] * 0.5],
                'hard': [difficulty_counts['hard'] * 0.4, difficulty_counts['hard'] * 0.3,
                         difficulty_counts['hard'] * 0.3]
            }

            # Convert to numpy arrays for stacking
            letter_hints = [hint_data[level][0] for level in difficulty_levels]
            word_hints = [hint_data[level][1] for level in difficulty_levels]
            no_hints = [hint_data[level][2] for level in difficulty_levels]

            width = 0.6
            ax4.bar(difficulty_levels, letter_hints, width, label='Letter Hint', color='#42A5F5')
            ax4.bar(difficulty_levels, word_hints, width, bottom=letter_hints, label='Word Hint', color='#7E57C2')
            ax4.bar(difficulty_levels, no_hints, width, bottom=np.array(letter_hints) + np.array(word_hints),
                    label='No Hint', color='#78909C')

            ax4.set_title('Hint Usage Across Difficulty Levels', fontsize=14)
            ax4.set_xlabel('Difficulty Level', fontsize=12)
            ax4.set_ylabel('Hint Usage Count', fontsize=12)
            ax4.legend()
            ax4.grid(axis='y', linestyle='--', alpha=0.7)

            fig4.tight_layout()
            canvas4 = FigureCanvasTkAgg(fig4, hint_tab)
            canvas4.draw()
            canvas4.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 5. Time Taken per Round - Line Graph
            time_tab = ttk.Frame(notebook)
            notebook.add(time_tab, text="Time Taken per Round")
            fig5 = plt.Figure(figsize=(7, 5), dpi=100)
            ax5 = fig5.add_subplot(111)

            # Calculate average time taken by difficulty
            time_stats = df.groupby('difficulty')['time_taken'].agg(['mean', 'min', 'max']).reset_index()
            time_stats = time_stats.set_index('difficulty').reindex(difficulty_order).reset_index()
            time_stats = time_stats.fillna(0)

            # Plot average time with error bars from min to max
            x = range(len(difficulty_order))
            ax5.plot(x, time_stats['mean'], 'o-', linewidth=2, markersize=8, color='#FF5722', label='Average Time')

            # Add error bars from min to max
            for i, (_, row) in enumerate(time_stats.iterrows()):
                ax5.plot([i, i], [row['min'], row['max']], 'k-', alpha=0.3)
                ax5.plot(i, row['min'], '_', color='blue', markersize=10)
                ax5.plot(i, row['max'], '_', color='red', markersize=10)
                ax5.text(i, row['mean'] + 2, f"{row['mean']:.1f}s", ha='center')

            ax5.set_title('Distribution of Time Taken per Round', fontsize=14)
            ax5.set_xlabel('Difficulty Level', fontsize=12)
            ax5.set_ylabel('Time Taken (seconds)', fontsize=12)
            ax5.set_xticks(x)
            ax5.set_xticklabels(difficulty_order)
            ax5.grid(True, linestyle='--', alpha=0.7)
            ax5.legend()

            fig5.tight_layout()
            canvas5 = FigureCanvasTkAgg(fig5, time_tab)
            canvas5.draw()
            canvas5.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Add an export button to save statistics
            def export_stats():
                try:
                    export_dir = 'stats_exports'
                    os.makedirs(export_dir, exist_ok=True)

                    # Generate a timestamp for the filename
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{export_dir}/wordle_stats_{timestamp}.csv"

                    # Export summary statistics
                    summary = pd.DataFrame({
                        'Metric': ['Games Played', 'Games Won', 'Success Rate (%)', 'Average Attempts',
                                   'Average Time (s)'],
                        'Value': [games_played, games_won, success_rate, avg_attempts, avg_time]
                    })

                    summary.to_csv(filename, index=False)
                    messagebox.showinfo("Export Complete", f"Statistics exported to {filename}")
                except Exception as e:
                    messagebox.showerror("Export Error", f"Could not export statistics: {e}")

            export_button = tk.Button(stats_window, text="Export Statistics", command=export_stats)
            export_button.pack(pady=10)

        except ImportError as e:
            # Fall back to simple message if visualization libraries aren't available
            messagebox.showinfo("Error", f"Could not load required libraries: {e}")

        except Exception as e:
            # Handle any other errors
            messagebox.showerror("Error", f"An error occurred while loading statistics: {e}")
