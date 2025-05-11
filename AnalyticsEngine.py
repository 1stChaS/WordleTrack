import csv
import os

class AnalyticsEngine:
    """Collects and processes gameplay statistical data."""

    def __init__(self):
        """Initialize analytics tracking system."""
        self.games_played = 0
        self.games_won = 0
        self.guess_attempts = []
        self.game_times = []
        self.word_difficulty = {}
        self.letter_success = {}
        self.letter_positions = {}
        self.difficulty_stats = {
            'easy': {'played': 0, 'won': 0, 'avg_attempts': 0},
            'medium': {'played': 0, 'won': 0, 'avg_attempts': 0},
            'hard': {'played': 0, 'won': 0, 'avg_attempts': 0}
        }
        self.word_length_stats = {}  # {length: {'played': x, 'won': y, 'avg_attempts': z}}
        self.first_letters = {}
        self.difficulty_changes = []
        self.letter_frequency = {letter: 0 for letter in 'abcdefghijklmnopqrstuvwxyz'}
        self.time_vs_attempts = []
        self.streak_history = []

    def log_game_to_csv(self, word, attempts, success, time_taken, difficulty='medium', hints_used=0,
                        csv_file='data/history/history_record.csv'):
        """
        Logs a game result to a CSV file for persistent tracking.

        Parameters:
            word (str): The target word of the game.
            attempts (int): Number of guesses used.
            success (bool): Whether the word was guessed.
            time_taken (float): Time taken in seconds.
            difficulty (str): Difficulty level ('easy', 'medium', 'hard').
            hints_used (int): Number of hints used during the game.
            csv_file (str): Output CSV file path.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)

        # Check if file exists and determine the next game number
        file_exists = os.path.isfile(csv_file)

        if file_exists:
            # Read the existing file to find the highest game number
            try:
                with open(csv_file, 'r') as file:
                    reader = csv.reader(file)
                    next(reader)  # Skip header
                    game_numbers = [int(row[0]) for row in reader if row and row[0].isdigit()]
                    next_game_number = max(game_numbers) + 1 if game_numbers else 1
            except (IndexError, ValueError):
                # Handle cases where file might be empty or corrupted
                next_game_number = 1
        else:
            next_game_number = 1

        # Write the new game record
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(
                    ['game_number', 'word_length', 'word', 'attempts', 'result', 'time_taken', 'difficulty',
                     'hints_used'])

            writer.writerow([
                next_game_number,
                len(word),
                word,
                attempts,
                'win' if success else 'loss',
                round(time_taken, 2),
                difficulty,
                hints_used
            ])

        # Update the games_played attribute
        self.games_played = next_game_number

    def record_game(self, word, attempts, success, time_taken, difficulty='medium', hints_used=0):
        """
        Record data from a completed game.
        Parameters: word (str): The target word
        attempts (int): Number of attempts made
        success (bool): Whether the player guessed correctly
        time_taken (float): Time taken in seconds
        difficulty (str): Game difficulty level ('easy', 'medium', 'hard')
        hints_used (int): Number of hints used during the game
        """
        self.games_played += 1
        self.time_vs_attempts.append((time_taken, attempts, success))

        if success:
            self.games_won += 1
            self.guess_attempts.append(attempts)
        else:
            self.guess_attempts.append(attempts)
        self.game_times.append(time_taken)

        # track word difficulty
        if word in self.word_difficulty:
            # update average attempts
            prev_count = self.word_difficulty[word]['count']
            prev_avg = self.word_difficulty[word]['avg_attempts']
            new_avg = (prev_avg * prev_count + attempts) / (prev_count + 1)
            self.word_difficulty[word] = {
                'count': prev_count + 1,
                'avg_attempts': new_avg
            }
        else:
            self.word_difficulty[word] = {
                'count': 1,
                'avg_attempts': attempts
            }
        # update difficulty level stats
        diff = difficulty.lower()
        if diff in self.difficulty_stats:
            self.difficulty_stats[diff]['played'] += 1
            if success:
                self.difficulty_stats[diff]['won'] += 1
            # update ave attempts
            prev_count = self.difficulty_stats[diff]['played'] - 1
            prev_avg = self.difficulty_stats[diff]['avg_attempts']
            new_avg = (prev_avg * prev_count + attempts) / self.difficulty_stats[diff]['played']
            self.difficulty_stats[diff]['avg_attempts'] = new_avg

        length = len(word)
        if length not in self.word_length_stats:
            self.word_length_stats[length] = {'played': 0, 'won': 0, 'avg_attempts': 0}

        stats = self.word_length_stats[length]
        stats['played'] += 1
        if success:
            stats['won'] += 1
        prev_avg = stats['avg_attempts']
        prev_count = stats['played'] - 1
        new_avg = (prev_avg * prev_count + attempts) / stats['played']
        stats['avg_attempts'] = new_avg

        # record in each round in csv
        self.log_game_to_csv(word, attempts, success, time_taken, difficulty, hints_used)

    def record_letter_feedback(self, letter, position, status):
        """
        Record feedback for a specific letter in a specific position.

        Parameters: letter (str): The letter
                    position (int): Position in the word (0-based)
                    status (str): 'correct', 'present', or 'absent'
        """
        # Initialize letter tracking if needed
        if letter not in self.letter_success:
            self.letter_success[letter] = {
                'attempts': 0,
                'correct': 0,
                'present': 0
            }
        if position not in self.letter_positions:
            self.letter_positions[position] = {}
        if letter not in self.letter_positions[position]:
            self.letter_positions[position][letter] = {
                'attempts': 0,
                'correct': 0
            }
        # update letter stats
        self.letter_success[letter]['attempts'] += 1
        if status in ('correct', 'present'):
            self.letter_success[letter][status] += 1

        # update position stats
        self.letter_positions[position][letter]['attempts'] += 1
        if status == 'correct':
            self.letter_positions[position][letter]['correct'] += 1

    def record_guess(self, guess, difficulty):
        # track first letters
        first_letter = guess[0].lower()
        self.first_letters[first_letter] = self.first_letters.get(first_letter, 0) + 1

        # track letter frequency
        for letter in set(guess.lower()):
            if letter in self.letter_frequency:
                self.letter_frequency[letter] += 1

    def calculate_letter_success(self):
        """
        Calculate success rates for letters.
        Returns: dict: Letter success statistics
        """
        results = {}
        for letter, stats in self.letter_success.items():
            if stats['attempts'] > 0:
                correct_rate = stats['correct'] / stats['attempts']
                present_rate = stats['present'] / stats['attempts']
                results[letter] = {
                    'correct_rate': correct_rate,
                    'present_rate': present_rate,
                    'overall_rate': (stats['correct'] + stats['present']) / stats['attempts'],
                    'attempts': stats['attempts']
                }
        return results

    def calculate_position_success(self):
        """
        Calculate success rates for letters in each position.
        Returns: dict: Position-based letter success statistics
        """
        results = {}
        for position, letters in self.letter_positions.items():
            results[position] = {}
            for letter, stats in letters.items():
                if stats['attempts'] > 0:
                    correct_rate = stats['correct'] / stats['attempts']
                    results[position][letter] = {
                        'correct_rate': correct_rate,
                        'attempts': stats['attempts']
                    }
        return results

    def get_most_challenging_words(self, count=5):
        """
        Get the most challenging words based on average attempts.
        Parameters: count (int): Number of words to return
        Returns: list: List of (word, avg_attempts) tuples
        """
        # filter words with at least 2 attempts
        eligible_words = {word: stats['avg_attempts']
                          for word, stats in self.word_difficulty.items()
                          if stats['count'] >= 2}
        # Sort ave attempts (descending)
        sorted_words = sorted(eligible_words.items(), key=lambda x: x[1], reverse=True)
        return sorted_words[:count]

    def get_easiest_words(self, count=5):
        """
        Get the easiest words based on average attempts.
        Parameters: count (int): Number of words to return
        Returns: list: List of (word, avg_attempts) tuples
        """
        # filter words with at least 2 attempts
        eligible_words = {word: stats['avg_attempts']
                          for word, stats in self.word_difficulty.items()
                          if stats['count'] >= 2}
        # Sort ave attempts (ascending)
        sorted_words = sorted(eligible_words.items(), key=lambda x: x[1])
        return sorted_words[:count]

    def get_performance_trend(self, window_size=5):
        """
        Calculate performance trend over recent games.
        Parameters: window_size (int): Number of recent games to analyze
        Returns: dict: Performance trend statistics
        """
        if len(self.guess_attempts) < window_size:
            return None
        # most recent games
        recent_attempts = self.guess_attempts[-window_size:]
        recent_times = self.game_times[-window_size:]

        # previous set of games
        if len(self.guess_attempts) >= (window_size * 2):
            prev_attempts = self.guess_attempts[-(window_size * 2):-window_size]
            prev_times = self.game_times[-(window_size * 2):-window_size]
        else:
            prev_attempts = self.guess_attempts[:len(self.guess_attempts) - window_size]
            prev_times = self.game_times[:len(self.game_times) - window_size]

        # No games before
        if not prev_attempts:
            return None

        # calculate averages
        recent_avg_attempts = sum(recent_attempts) / len(recent_attempts)
        recent_avg_time = sum(recent_times) / len(recent_times)
        prev_avg_attempts = sum(prev_attempts) / len(prev_attempts)
        prev_avg_time = sum(prev_times) / len(prev_times)

        # Calculate trends
        attempt_trend = recent_avg_attempts - prev_avg_attempts
        time_trend = recent_avg_time - prev_avg_time
        return {
            'attempt_trend': attempt_trend,
            'time_trend': time_trend,
            'recent_avg_attempts': recent_avg_attempts,
            'recent_avg_time': recent_avg_time
        }

    def generate_report(self):
        """
        Generate a comprehensive report of player performance.
        Returns: dict or str: Statistical report or message if not enough data
        """
        if self.games_played == 0:
            return "No game data available yet."
        success_rate = (self.games_won / self.games_played) * 100 if self.games_played > 0 else 0
        avg_attempts = sum(self.guess_attempts) / len(self.guess_attempts) if self.guess_attempts else 0
        avg_time = sum(self.game_times) / len(self.game_times) if self.game_times else 0

        challenging_words = self.get_most_challenging_words(3)
        easy_words = self.get_easiest_words(3)

        trend = self.get_performance_trend()
        report = {
            'games_played': self.games_played,
            'games_won': self.games_won,
            'success_rate': success_rate,
            'avg_attempts': avg_attempts,
            'avg_time': avg_time,
            'difficulty_stats': self.difficulty_stats,
        }
        if challenging_words:
            report['challenging_words'] = challenging_words
        if easy_words:
            report['easy_words'] = easy_words
        if trend:
            report['trend'] = trend
        return report

    def get_letter_frequency_stats(self):
        """
        Get statistics on the frequency and success rate of letters.
        Returns: dict: Letter frequency and success statistics
        """
        if not self.letter_success:
            return None
        stats = {}
        for letter, data in self.letter_success.items():
            if data['attempts'] > 0:
                stats[letter] = {
                    'frequency': data['attempts'],
                    'correct_rate': data['correct'] / data['attempts'],
                    'present_rate': data['present'] / data['attempts']
                }
        return stats

    def get_difficulty_recommendation(self):
        """
        Generate a recommendation for difficulty level based on player performance.
        Returns: str: Difficulty recommendation
        """
        if self.games_played < 5:
            return "Play more games to get a personalized difficulty recommendation."

        # success rate
        success_rate = (self.games_won / self.games_played) * 100
        # average attempts
        avg_attempts = sum(self.guess_attempts) / len(self.guess_attempts)
        # trend
        trend = self.get_performance_trend()
        improving = trend and trend['attempt_trend'] < 0

        # recommendation
        if success_rate < 20:
            return "Consider trying Easy difficulty to build confidence."
        elif success_rate > 80 and avg_attempts < 3:
            return "You're doing great! Challenge yourself with Hard difficulty."
        elif improving:
            return "You're improving! Continue with your current difficulty or try one level higher."
        elif success_rate > 50:
            return "You're doing well at your current difficulty level."
        else:
            return "Keep practicing at this level to improve your skills."
