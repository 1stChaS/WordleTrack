class HintSystem:
    """Provides intelligent hints to help players during the game."""

    def __init__(self):
        self.player_history = []
        self.current_word = ""
        self.yellow_letters = {}
        self.correct_letters = {}
        self.incorrect_letters = set()

    def set_current_word(self, word):
        """Set the current target word and reset history."""
        self.current_word = word.lower()
        self.player_history = []
        self.yellow_letters = {}
        self.correct_letters = {}
        self.incorrect_letters = set()

    def record_attempt(self, guess, feedback):
        """
        Record a player's guess and the resulting feedback.

        Parameters: guess (str): The player's guess
                    feedback (list): List of feedback ('correct', 'present', 'absent') for each letter
        """
        self.player_history.append((guess.lower(), feedback))
        self._update_letter_constraints(guess.lower(), feedback)

    def _update_letter_constraints(self, guess, feedback):
        """Update letter constraints based on the latest guess and feedback."""
        for i, (letter, status) in enumerate(zip(guess, feedback)):
            if status == 'correct':
                self.correct_letters[i] = letter
                if letter in self.yellow_letters:
                    if i in self.yellow_letters[letter]:
                        self.yellow_letters[letter].remove(i)

            elif status == 'present':
                if letter not in self.yellow_letters:
                    self.yellow_letters[letter] = [pos for pos in range(len(guess)) if pos != i]
                else:
                    if i in self.yellow_letters[letter]:
                        self.yellow_letters[letter].remove(i)

            elif status == 'absent':
                letter_elsewhere = False
                for prev_guess, prev_feedback in self.player_history:
                    for j, (prev_letter, prev_status) in enumerate(zip(prev_guess, prev_feedback)):
                        if prev_letter == letter and (prev_status == 'correct' or prev_status == 'present'):
                            letter_elsewhere = True
                            break
                    if letter_elsewhere:
                        break
                if not letter_elsewhere:
                    self.incorrect_letters.add(letter)

    def sort_hint(self, last_attempt):
        """
        Use constraint propagation to reposition yellow-marked characters
        in their correct positions.
        Parameters: last_attempt (str): The most recent guess
        Returns: str: A suggestion for repositioning yellow letters
        """
        if not self.player_history:
            return "No previous attempts to analyze."

        last_guess, last_feedback = self.player_history[-1]

        # yellow position
        yellow_positions = [i for i, status in enumerate(last_feedback) if status == 'present']
        if not yellow_positions:
            return "No yellow letters to sort in the last attempt."
        yellow_letters = [last_guess[i] for i in yellow_positions]

        # correct position
        template = ['_'] * len(last_guess)
        for pos, letter in self.correct_letters.items():
            template[pos] = letter

        # suggest to press yellow position
        suggestion = self.find_best_positions(template, yellow_letters, yellow_positions)
        if suggestion:
            return f"Try this arrangement: {suggestion}"
        else:
            return f"Keep these letters but try different positions: {''.join(yellow_letters)}"

    def find_best_positions(self, template, yellow_letters, current_positions):
        """
        Find the best positions for yellow letters.
        Uses constraint satisfaction to place yellow letters in valid positions.
        """
        word_length = len(template)

        # get open positions (not green)
        open_positions = [i for i in range(word_length) if template[i] == '_']

        # not enough open positions for all yellow letters
        if len(open_positions) < len(yellow_letters):
            return None

        # place each yellow letter in a valid position
        result = template.copy()
        placed = set()

        # place letters with few options
        for letter in yellow_letters:
            if letter in self.yellow_letters:
                valid_positions = [pos for pos in self.yellow_letters[letter] if
                                   pos in open_positions and pos not in placed]
                if len(valid_positions) == 1:
                    pos = valid_positions[0]
                    result[pos] = letter
                    placed.add(pos)
                    open_positions.remove(pos)

        # place remaining letters
        remaining_letters = [l for l in yellow_letters if
                             l not in [result[i] for i in range(word_length) if result[i] != '_']]
        remaining_positions = [pos for pos in open_positions if pos not in placed]
        for i, letter in enumerate(remaining_letters):
            if i < len(remaining_positions):
                result[remaining_positions[i]] = letter

        return ''.join(result)

    def analyze_past_guesses(self):
        """
        Analyze patterns in past guesses to identify potential strategies.
        Returns: str: Analysis of past guesses and suggestions
        """
        if len(self.player_history) < 2:
            return "Need more guesses to analyze patterns."

        letter_freq = {}
        for guess, _ in self.player_history:
            for letter in guess:
                letter_freq[letter] = letter_freq.get(letter, 0) + 1

        # find most frequently guessed letters
        common_letters = sorted(letter_freq.items(), key=lambda x: x[1], reverse=True)[:3]

        # check if player is repeating incorrect patterns
        repeated_patterns = self._find_repeated_patterns()

        analysis = "Analysis of your guesses:\n"

        if repeated_patterns:
            analysis += f"- You've repeated these incorrect patterns: {', '.join(repeated_patterns)}\n"

        analysis += f"- Most used letters: {', '.join([f'{l[0]} ({l[1]}x)' for l in common_letters])}\n"

        # give advice based on letter distribution
        used_vowels = [l for l in "aeiou" if l in letter_freq]
        if len(used_vowels) < 3:
            analysis += "- Try using more vowels in your guesses\n"

        return analysis

    def _find_repeated_patterns(self):
        """Find repeated incorrect letter patterns in guesses."""
        patterns = []

        # find repeated letter pairs that don't work
        pair_attempts = {}
        for guess, feedback in self.player_history:
            for i in range(len(guess) - 1):
                if feedback[i] != 'correct' and feedback[i + 1] != 'correct':
                    pair = guess[i:i + 2]
                    pair_attempts[pair] = pair_attempts.get(pair, 0) + 1

        # unsuccessfully pair
        repeated_pairs = [pair for pair, count in pair_attempts.items() if count > 1]
        if repeated_pairs:
            patterns.extend(repeated_pairs)
        return patterns

    def generate_hint(self):
        """
        Generate a helpful hint based on the current game state.
        Returns: str: A hint to help the player
        """
        if not self.player_history:
            return "Try starting with words that have common letters like E, A, R, I, O, T."

        # Choose hint type based on game progress
        num_attempts = len(self.player_history)
        if num_attempts == 1:
            # the letters they should avoid
            if self.incorrect_letters:
                return f"Avoid these letters: {', '.join(sorted(self.incorrect_letters))}"
            else:
                return "Good start! Try to use different letters in your next guess."

        elif num_attempts == 2:
            # correct letter positions
            if self.correct_letters:
                positions = []
                for pos, letter in sorted(self.correct_letters.items()):
                    positions.append(f"{letter.upper()} at position {pos + 1}")
                return f"You've correctly placed: {', '.join(positions)}"
            elif self.yellow_letters:
                return self.sort_hint(self.player_history[-1][0])

        elif num_attempts == 3:
            # possible words
            return self._suggest_possible_word_pattern()

        else:
            if self.yellow_letters and num_attempts % 2 == 0:
                return self.sort_hint(self.player_history[-1][0])
            else:
                return self._suggest_letter()

    def _suggest_possible_word_pattern(self):
        """Suggest a pattern for possible words."""
        pattern = ['_'] * len(self.current_word)
        for pos, letter in self.correct_letters.items():
            pattern[pos] = letter.upper()
        pattern_str = ' '.join(pattern)
        if self.yellow_letters:
            yellow_info = ", ".join([f"{letter.upper()} (positions: {', '.join([str(pos + 1) for pos in positions])})"
                                     for letter, positions in self.yellow_letters.items()])
            return f"Word pattern: {pattern_str}\nYou need to place: {yellow_info}"
        else:
            return f"Word pattern: {pattern_str}"

    def _suggest_letter(self):
        """Suggest a specific letter to try."""
        word_length = len(self.current_word)
        # common letters
        common_letters = "etaoinsrhdlucmfywgpbvkjxqz"

        # filter out letters already tried
        tried_letters = set()
        for guess, _ in self.player_history:
            tried_letters.update(guess)

        # find the most common letter
        for letter in common_letters:
            if letter not in tried_letters and letter not in self.incorrect_letters:
                return f"Try a word with the letter '{letter.upper()}'."
        # analyze past guesses
        return self.analyze_past_guesses()
