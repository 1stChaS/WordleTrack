import os
import json


class DataManager:
    """Handles all data persistence for the game."""

    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        # Player data file
        self.player_file = os.path.join(data_dir, "player_data.json")
        self._init_player_file()

        # Config file
        self.config_file = os.path.join(data_dir, "config.json")
        self._init_config_file()

        # Game history file
        self.history_file = os.path.join(data_dir, "game_history.json")
        self._init_history_file()

    def _init_player_file(self):
        """Initialize player data file with new structure"""
        if not os.path.exists(self.player_file):
            with open(self.player_file, 'w') as f:
                json.dump({
                    "players": {
                        "Player": {
                            "summary": {
                                "games_played": 0,
                                "games_won": 0,
                                "total_attempts": 0,
                                "total_time": 0,
                                "hints_used": 0,
                                "streak": 0,
                                "max_streak": 0
                            },
                            "game_history": []
                        }
                    },
                    "global_stats": {
                        "total_games": 0,
                        "total_wins": 0,
                        "total_hints_used": 0,
                        "current_streak": 0,
                        "max_streak": 0
                    }
                }, f, indent=4)

    def _init_config_file(self):
        """Initialize config file with defaults if it doesn't exist."""
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as f:
                json.dump({
                    "word_length": 5,
                    "max_attempts": 6,
                    "difficulty": "medium",
                    "colors": {
                        "correct": "#6aaa64",
                        "present": "#c9b458",
                        "absent": "#787c7e",
                        "default": "#ffffff",
                        "text": "#000000"
                    }
                }, f, indent=4)

    def _init_history_file(self):
        """Initialize game history file if it doesn't exist."""
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)

    def save_player_data(self, player_name, game_data):
        """Save both individual game records and update summary statistics"""
        try:
            # Load existing data
            if os.path.exists(self.player_file):
                with open(self.player_file, 'r') as f:
                    all_data = json.load(f)
            else:
                all_data = {
                    "players": {},
                    "global_stats": {
                        "total_games": 0,
                        "total_wins": 0,
                        "total_hints_used": 0,
                        "current_streak": 0,
                        "max_streak": 0
                    }
                }

            # Initialize player if not exists
            if player_name not in all_data["players"]:
                all_data["players"][player_name] = {
                    "summary_stats": {
                        "games_played": 0,
                        "games_won": 0,
                        "total_attempts": 0,
                        "total_time": 0,
                        "hints_used": 0,
                        "current_streak": 0,
                        "max_streak": 0
                    },
                    "game_records": []
                }

            player_entry = all_data["players"][player_name]

            # Add new game record
            player_entry["game_records"].append({
                "word": game_data["word"],
                "attempts": game_data["attempts"],
                "success": game_data["success"],
                "time_taken": game_data["time_taken"],
                "hints_used": game_data["hints_used"],
                "timestamp": game_data.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S")),
                "difficulty": game_data.get("difficulty", "medium")
            })

            # Update summary stats
            summary = player_entry["summary_stats"]
            summary["games_played"] += 1
            summary["total_attempts"] += game_data["attempts"]
            summary["total_time"] += game_data["time_taken"]
            summary["hints_used"] += game_data["hints_used"]

            if game_data["success"]:
                summary["games_won"] += 1
                summary["current_streak"] += 1
                if summary["current_streak"] > summary["max_streak"]:
                    summary["max_streak"] = summary["current_streak"]
            else:
                summary["current_streak"] = 0

            # Update global stats
            global_stats = all_data["global_stats"]
            global_stats["total_games"] += 1
            global_stats["total_hints_used"] += game_data["hints_used"]
            if game_data["success"]:
                global_stats["total_wins"] += 1
                global_stats["current_streak"] += 1
                if global_stats["current_streak"] > global_stats["max_streak"]:
                    global_stats["max_streak"] = global_stats["current_streak"]
            else:
                global_stats["current_streak"] = 0

            # Save back to file
            with open(self.player_file, 'w') as f:
                json.dump(all_data, f, indent=4)

            return True
        except Exception as e:
            print(f"Error saving player data: {e}")
            return False

    def load_player_data(self, player_name):
        """Load player data, returning defaults if player doesn't exist."""
        try:
            with open(self.player_file, 'r') as f:
                all_data = json.load(f)
                return all_data["players"].get(player_name, {
                    "games_played": 0,
                    "games_won": 0,
                    "total_attempts": 0,
                    "total_time": 0,
                    "hints_used": 0,
                    "streak": 0,
                    "max_streak": 0
                })
        except Exception as e:
            print(f"Error loading player data: {e}")
            return {
                "games_played": 0,
                "games_won": 0,
                "total_attempts": 0,
                "total_time": 0,
                "hints_used": 0,
                "streak": 0,
                "max_streak": 0
            }

    def save_config(self, config_data):
        """Save configuration data, preserving any unspecified settings."""
        try:
            # Load existing config first
            existing_config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    existing_config = json.load(f)

            # Merge new config with existing
            merged_config = {**existing_config, **config_data}

            # Save merged config
            with open(self.config_file, 'w') as f:
                json.dump(merged_config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def load_config(self):
        """Load configuration data with defaults for missing values."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config, using defaults: {e}")
            return {
                "word_length": 5,
                "max_attempts": 6,
                "difficulty": "medium",
                "colors": {
                    "correct": "#6aaa64",
                    "present": "#c9b458",
                    "absent": "#787c7e",
                    "default": "#ffffff",
                    "text": "#000000"
                }
            }

    def record_game_history(self, game_data):
        """Append game history data to the history file."""
        try:
            # Load existing history
            history = []
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    history = json.load(f)

            # Append new game data
            history.append(game_data)

            # Save back to file
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=4)
            return True
        except Exception as e:
            print(f"Error recording game history: {e}")
            return False

    def get_game_history(self, limit=None):
        """Retrieve game history, optionally limited to most recent entries."""
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
                if limit and len(history) > limit:
                    return history[-limit:]
                return history
        except Exception as e:
            print(f"Error loading game history: {e}")
            return []
