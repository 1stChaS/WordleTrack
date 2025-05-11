import csv
import random
import os


class WordBank:
    """Stores words and selects words dynamically."""

    def __init__(self):
        self.word_list = []
        self.word_set = set()  # For faster lookups
        self.word_by_length = {}
        self.difficulty_mapping = {
            5: {
                'easy': {'min_freq': 0.8, 'max_unique': 3},
                'medium': {'min_freq': 0.5, 'max_unique': 4},
                'hard': {'min_freq': 0.0, 'max_unique': 5}
            },
            4: {
                'easy': {'min_freq': 0.75, 'max_unique': 3},
                'medium': {'min_freq': 0.4, 'max_unique': 3},
                'hard': {'min_freq': 0.0, 'max_unique': 4}
            }
        }
        self.load_words()

    def load_words(self):
        """Load words from CSV files for different word lengths"""
        five_letter_path = "data/wordle/word_5.csv"
        four_letter_path = "data/wordle/word_4.csv"

        if os.path.exists(five_letter_path):
            self._load_5_letter_words(five_letter_path)
        if os.path.exists(four_letter_path):
            self._load_4_letter_words(four_letter_path)

        print(f"Loaded {len(self.word_list)} words total")
        print(
            f"Words by length: {', '.join([f'{length}: {len(words)}' for length, words in self.word_by_length.items()])}")

    def _load_5_letter_words(self, csv_filename):
        """Load 5-letter words from CSV file with headers"""
        try:
            with open(csv_filename, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    word = row['Word'].lower()
                    self._add_word(word)
        except Exception as e:
            print(f"Error loading 5-letter words: {e}")

    def _load_4_letter_words(self, filename):
        """Load 4-letter words from a simple list file"""
        try:
            with open(filename, mode='r') as file:
                for line in file:
                    word = line.strip().lower()
                    if len(word) == 4:  # Ensure it's a 4-letter word
                        self._add_word(word)
        except Exception as e:
            print(f"Error loading 4-letter words: {e}")

    def _add_word(self, word):
        """Add a word to the appropriate collections"""
        self.word_list.append(word)
        self.word_set.add(word)

        # Group words by length
        length = len(word)
        if length not in self.word_by_length:
            self.word_by_length[length] = []
        self.word_by_length[length].append(word)

    def get_random_word(self, difficulty='medium', word_length=5):
        """
        Select a random word based on difficulty level and word length

        Parameters: difficulty (str): 'easy', 'medium', or 'hard'
                    word_length (int): Length of the word to select

        Returns: str: A word of the specified length and difficulty
        """
        # Check if we have words of the requested length
        if word_length in self.word_by_length and self.word_by_length[word_length]:
            available_words = self.word_by_length[word_length]
        else:
            print(f"No words of length {word_length} available, using default word list")
            available_words = self.word_list

        # If we don't have difficulty mapping for this word length, use medium settings
        if word_length not in self.difficulty_mapping:
            print(f"No difficulty mapping for {word_length}-letter words, using default")
            diff_params = {'min_freq': 0.5, 'max_unique': word_length - 1}
        else:
            diff_params = self.difficulty_mapping[word_length].get(difficulty,
                                                                   self.difficulty_mapping[word_length]['medium'])

        # Filter words by difficulty criteria
        suitable_words = []
        for word in available_words:
            unique_letters = len(set(word))

            # frequency calculation - common letters in English
            common_letters = set("etaoinshrdlu")
            letter_commonality = sum(1 for letter in word if letter in common_letters) / len(word)

            # Apply difficulty criteria
            if difficulty == 'easy':
                # Easy: More common letters and fewer unique letters
                if (unique_letters <= diff_params['max_unique'] and
                        letter_commonality >= diff_params['min_freq']):
                    suitable_words.append(word)
            elif difficulty == 'medium':
                # Medium: Balanced between common and uncommon letters
                if (unique_letters <= diff_params['max_unique'] and
                        letter_commonality >= diff_params['min_freq']):
                    suitable_words.append(word)
            elif difficulty == 'hard':
                # Hard: More unique letters and possibly uncommon letters
                if unique_letters >= word_length - 1 or letter_commonality < 0.5:
                    suitable_words.append(word)

        # If no suitable words found, fallback to any word of the correct length
        if not suitable_words and available_words:
            print(f"No suitable {difficulty} words of length {word_length}, using random selection")
            return random.choice(available_words)

        return random.choice(suitable_words) if suitable_words else random.choice(self.word_list)

    def validate_word(self, guess):
        """Check if a word exists in the word bank"""
        return guess.lower() in self.word_set
