class HintSystem:
    """Provides intelligent hints to help players during the game."""

    def __init__(self):
        self.player_history = []
        self.current_word = ""
        self.yellow_letters = {}
        self.correct_letters = {}
        self.incorrect_letters = set()
        self.last_hint = ""  # Track the last hint given to avoid repetition
        self.word_length = 0

    def set_current_word(self, word):
        """Set the current target word and reset history."""
        self.current_word = word.lower()
        self.word_length = len(word)
        self.player_history = []
        self.yellow_letters = {}
        self.correct_letters = {}
        self.incorrect_letters = set()
        self.last_hint = ""

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
                # Clean up yellow_letters if this letter was previously yellow
                if letter in self.yellow_letters:
                    if i in self.yellow_letters[letter]:
                        self.yellow_letters[letter].remove(i)
                    # If no more possible positions for this yellow letter, remove it
                    if not self.yellow_letters[letter]:
                        del self.yellow_letters[letter]

            elif status == 'present':
                if letter not in self.yellow_letters:
                    self.yellow_letters[letter] = [pos for pos in range(self.word_length) if pos != i]
                else:
                    if i in self.yellow_letters[letter]:
                        self.yellow_letters[letter].remove(i)

            elif status == 'absent':
                # Check if the letter appears elsewhere (as yellow or green)
                letter_elsewhere = False
                for prev_guess, prev_feedback in self.player_history:
                    for j, (prev_letter, prev_status) in enumerate(zip(prev_guess, prev_feedback)):
                        if prev_letter == letter and (prev_status == 'correct' or prev_status == 'present'):
                            letter_elsewhere = True
                            break
                    if letter_elsewhere:
                        break

                # Only add to incorrect_letters if the letter doesn't appear elsewhere
                if not letter_elsewhere:
                    self.incorrect_letters.add(letter)

    def sort_hint(self, last_attempt):
        """
        Create a template showing all correct letters in their right positions based on the secret word.
        - Green letters remain in their correct positions
        - Yellow letters are moved to their CORRECT positions according to the secret word

        Parameters: last_attempt (str): The most recent guess
        Returns: str: A template showing the word with known letters in correct positions
        """
        if not self.player_history:
            return "No previous attempts to analyze."

        # Get the most recent guess and feedback
        last_guess, last_feedback = self.player_history[-1]

        # Start with a template of placeholders
        template = ['_'] * self.word_length

        # First, fill in the green letters (already correct)
        for i, status in enumerate(last_feedback):
            if status == 'correct':
                template[i] = last_guess[i]

        # Now handle yellow letters (correct letter, wrong position)
        yellow_letters = []
        for i, status in enumerate(last_feedback):
            if status == 'present':
                yellow_letters.append(last_guess[i])

        # For each yellow letter, find where it should go in the secret word
        for letter in yellow_letters:
            # Look through the secret word for positions of this letter
            for i, secret_char in enumerate(self.current_word):  # Changed from self.secret_word to self.current_word
                # If this position matches the letter and is still empty in our template
                if secret_char == letter and template[i] == '_':
                    template[i] = letter
                    break  # Only place each yellow letter once

        return ''.join(template)

    def find_best_positions(self, template, yellow_letters, current_positions):
        """
        Find the best positions for yellow letters.
        Uses constraint satisfaction to place yellow letters in valid positions.
        """
        # Get open positions (not green)
        open_positions = [i for i in range(self.word_length) if template[i] == '_']

        # Not enough open positions for all yellow letters
        if len(open_positions) < len(yellow_letters):
            return None

        # Place each yellow letter in a valid position
        result = template.copy()
        placed = set()

        # First place letters with few options
        for letter in yellow_letters:
            if letter in self.yellow_letters:
                valid_positions = [pos for pos in self.yellow_letters[letter] if
                                   pos in open_positions and pos not in placed]
                if valid_positions:
                    if len(valid_positions) == 1:
                        pos = valid_positions[0]
                        result[pos] = letter
                        placed.add(pos)
                        open_positions.remove(pos)

        # Place remaining letters
        remaining_letters = [l for l in yellow_letters if
                             l not in [result[i] for i in range(self.word_length) if result[i] != '_']]
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

        # Find most frequently guessed letters
        common_letters = sorted(letter_freq.items(), key=lambda x: x[1], reverse=True)[:3]

        # Check if player is repeating incorrect patterns
        repeated_patterns = self._find_repeated_patterns()

        analysis = "Analysis of your guesses:\n"

        if repeated_patterns:
            analysis += f"- You've repeated these incorrect patterns: {', '.join(repeated_patterns)}\n"

        analysis += f"- Most used letters: {', '.join([f'{l[0].upper()} ({l[1]}x)' for l in common_letters])}\n"

        # Give advice based on letter distribution
        used_vowels = [l for l in "aeiou" if l in letter_freq]
        if len(used_vowels) < 3:
            analysis += "- Try using more vowels in your guesses\n"

        # Find unused common letters that might be worth trying
        common_letters = "etaoinsrhdlucmfywgpb"
        unused_common = [l.upper() for l in common_letters
                         if l not in letter_freq and l not in self.incorrect_letters][:3]
        if unused_common:
            analysis += f"- Consider these common unused letters: {', '.join(unused_common)}\n"

        return analysis

    def _find_repeated_patterns(self):
        """Find repeated incorrect letter patterns in guesses."""
        patterns = []

        # Find repeated letter pairs that don't work
        pair_attempts = {}
        for guess, feedback in self.player_history:
            for i in range(len(guess) - 1):
                if feedback[i] != 'correct' and feedback[i + 1] != 'correct':
                    pair = guess[i:i + 2]
                    pair_attempts[pair] = pair_attempts.get(pair, 0) + 1

        # Get unsuccessfully tried pairs
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
            # First attempt suggestion based on word length and letter frequency
            if self.word_length <= 4:
                first_hint = ("For short words, try starting with common letters like E, A, R, T. "
                              f"Good first guesses for {self.word_length}-letter words include "
                              f"{'RATE' if self.word_length == 4 else 'EAT' if self.word_length == 3 else 'AT'}.")
            else:
                first_hint = ("Try starting with words that contain common letters like E, A, R, I, O, T, N, S, L. "
                              f"Words like {'STARE' if self.word_length >= 5 else 'TEAR'} or "
                              f"{'ROAST' if self.word_length >= 5 else 'LAST'} make good first guesses.")
            self.last_hint = first_hint
            return first_hint

        # Choose hint type based on game progress and avoid repeating the last hint
        num_attempts = len(self.player_history)

        # For late game attempts (5-6), prioritize giving direct help
        if num_attempts >= 5:
            # At this critical stage, we should be specific about possible solutions
            hint = self._give_critical_hint()
            if hint and hint != self.last_hint:
                self.last_hint = hint
                return hint

        # For attempts 2-4, rotate through different hint types
        hint_options = []

        # Option 1: Suggest letter placements for yellow letters
        if self.yellow_letters:
            yellow_hint = self.sort_hint(self.player_history[-1][0])
            if yellow_hint != self.last_hint:
                hint_options.append(yellow_hint)

        # Option 2: Show word pattern with correct letters
        if self.correct_letters:
            pattern_hint = self._suggest_possible_word_pattern()
            if pattern_hint != self.last_hint:
                hint_options.append(pattern_hint)

        # Option 3: Suggest new letters to try
        if num_attempts < 4:  # Only in early-mid game
            letter_hint = self._suggest_new_word()
            if letter_hint != self.last_hint:
                hint_options.append(letter_hint)

        # Option 4: Analyze patterns in guesses
        if num_attempts >= 3:
            analysis_hint = self.analyze_past_guesses()
            if analysis_hint != self.last_hint:
                hint_options.append(analysis_hint)

        # Choose a hint we haven't given recently
        for hint in hint_options:
            if hint != self.last_hint:
                self.last_hint = hint
                return hint

        # If we've exhausted all options without finding a new hint
        if hint_options:
            self.last_hint = hint_options[0]
            return hint_options[0]
        else:
            # Fallback if no good hints are available
            fallback = self._suggest_letter()
            self.last_hint = fallback
            return fallback

    def _give_critical_hint(self):
        """Provide more direct help in the late game (attempts 5-6)."""
        # Create the word pattern with all we know
        pattern = ['_'] * self.word_length
        for pos, letter in self.correct_letters.items():
            pattern[pos] = letter.upper()

        # Count how many positions we know
        known_positions = len(self.correct_letters)
        unknown_positions = self.word_length - known_positions

        # If we know most of the word, give a strong hint
        if known_positions >= 2 >= unknown_positions:
            # For very short words or when we have most letters, give away one position
            for i in range(self.word_length):
                if i not in self.correct_letters and self.current_word[i] not in self.yellow_letters:
                    real_letter = self.current_word[i].upper()
                    hint_pattern = pattern.copy()
                    hint_pattern[i] = f"[{real_letter}]"  # Bracketed to show it's revealed
                    return f"Critical hint: Try this pattern: {''.join(hint_pattern)}"

        # If we have yellow letters that need placing
        if self.yellow_letters:
            yellow_info = []
            for letter, positions in self.yellow_letters.items():
                # Find where this letter actually belongs in the solution
                true_pos = -1
                for i, char in enumerate(self.current_word):
                    if char == letter and i not in self.correct_letters:
                        true_pos = i
                        break

                if true_pos != -1:
                    yellow_info.append(f"{letter.upper()} belongs at position {true_pos + 1}")

            if yellow_info:
                return f"Critical hint: {''.join(pattern)} - {'; '.join(yellow_info)}"

        # If we've made little progress, reveal a new letter
        if known_positions < 2:
            for i in range(self.word_length):
                if i not in self.correct_letters:
                    pattern[i] = f"[{self.current_word[i].upper()}]"  # Reveal one letter
                    return f"Critical hint: One letter revealed: {''.join(pattern)}"

        return None  # No critical hint generated

    def _suggest_possible_word_pattern(self):
        """Suggest a pattern for possible words."""
        pattern = ['_'] * self.word_length
        for pos, letter in self.correct_letters.items():
            pattern[pos] = letter.upper()
        pattern_str = ' '.join(pattern)

        if self.yellow_letters:
            yellow_info = ", ".join([f"{letter.upper()} (not at position{' ' if len(positions) == 1 else 's '}"
                                     f"{', '.join([str(pos + 1) for pos in positions])})"
                                     for letter, positions in self.yellow_letters.items()])
            return f"Word pattern: {pattern_str}\nLetters to place: {yellow_info}"
        else:
            return f"Word pattern: {pattern_str}"

    def _suggest_letter(self):
        """Suggest a specific letter to try."""
        # Common letters by frequency
        common_letters = "etaoinsrhdlucmfywgpbvkjxqz"

        # Filter out letters already tried
        tried_letters = set()
        for guess, _ in self.player_history:
            tried_letters.update(guess)

        # Find the most common letter that hasn't been tried
        for letter in common_letters:
            if letter not in tried_letters and letter not in self.incorrect_letters:
                return f"Try including the letter '{letter.upper()}' in your next word."

        # If all common letters tried, analyze past guesses
        return self.analyze_past_guesses()

    def _suggest_new_word(self):
        """Suggest trying a completely new word to gather more information."""
        # Get all letters used so far
        used_letters = set()
        for guess, _ in self.player_history:
            used_letters.update(guess)

        # Common letters that haven't been used yet
        common_letters = "etaoinsrhdlucmfywgpb"
        unused_common = [l for l in common_letters if l not in used_letters and l not in self.incorrect_letters]

        # If we've used less than 15 unique letters, suggest using more
        if len(used_letters) < 15 and unused_common:
            suggested_letters = unused_common[:4]  # Recommend up to 4 new letters
            return (f"Try a completely new word with some of these unused common letters: "
                    f"{', '.join(l.upper() for l in suggested_letters)}. "
                    f"This will help eliminate more possibilities.")

        # If we've already tried many letters, focus on refining what we know
        elif self.yellow_letters or self.correct_letters:
            return self._suggest_possible_word_pattern()

        # Default to letter suggestion
        else:
            return self._suggest_letter()
