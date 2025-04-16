class Player:
    """Stores player performance data."""

    def __init__(self, name="Player"):
        """Initialize player with default values."""
        self.score = None
        self.name = name
        self.games_played = 0
        self.games_won = 0
        self.total_attempts = 0
        self.total_time = 0
        self.hints_used = 0
        self.game_history = []
        self.streak = 0
        self.max_streak = 0

    def record_attempt(self, word, attempts, success, time_taken):
        """
        Record data from a completed game.
        Parameters: word (str): The target word
                    attempts (int): Number of attempts made
                    success (bool): Whether the player guess it correct
                    time_taken (float): Time taken in seconds
        """
        self.games_played += 1
        self.total_attempts += attempts
        self.total_time += time_taken
        # successful games
        if success:
            self.games_won += 1
            self.streak += 1
            # Update max streak if current streak is higher
            if self.streak > self.max_streak:
                self.max_streak = self.streak
        else:
            # if loss reset streak
            self.streak = 0

        game_record = {
            'word': word,
            'attempts': attempts,
            'success': success,
            'time': time_taken,
            'hints_used': self.hints_used
        }
        self.game_history.append(game_record)
        # reset hints
        self.hints_used = 0

    def use_hint(self):
        """Record that a hint was used in the current game."""
        self.hints_used += 1

    def update_score(self, points):
        """Update player score with additional points."""
        self.score += points

    def get_stats(self):
        """
        Get player statistics.
        Returns: dict: Player statistics
        """
        stats = {
            'name': self.name,
            'games_played': self.games_played,
            'games_won': self.games_won,
            'win_rate': (self.games_won / self.games_played * 100) if self.games_played > 0 else 0,
            'avg_attempts': (self.total_attempts / self.games_played) if self.games_played > 0 else 0,
            'avg_time': (self.total_time / self.games_played) if self.games_played > 0 else 0,
            'current_streak': self.streak,
            'max_streak': self.max_streak
        }
        return stats

    def get_difficulty_level(self):
        """
        Calculate a recommended difficulty level based on player performance.
        Returns: str: Recommended difficulty level ('easy', 'medium', 'hard')
        """
        if self.games_played < 5:
            return 'medium'

        win_rate = (self.games_won / self.games_played) \
            if self.games_played > 0 else 0
        avg_attempts = (self.total_attempts / self.games_played) \
            if self.games_played > 0 else 0
        if win_rate > 0.8 and avg_attempts < 3.5:
            return 'hard'
        elif win_rate < 0.3:
            return 'easy'
        else:
            return 'medium'
