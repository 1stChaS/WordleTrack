import csv
import random


class WordBank:
    """Stores words and selects words dynamically."""

    def __init__(self, csv_filename="data/wordle/word_5.csv"):
        self.word_list = []
        self.word_set = set()  # For faster lookups
        self.csv_filename = csv_filename
        self.difficulty_mapping = {
            'easy': {'min_freq': 0.8, 'max_unique': 4},
            'medium': {'min_freq': 0.4, 'max_unique': 5}
        }
        self.word_by_length = {}
        self.load_words()

    def load_words(self):
        """Load words from CSV file"""
        # try:
        with open(self.csv_filename, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                word = row['Word'].lower()
                self.word_list.append(word)
                self.word_set.add(word)

                # Group words by length
                length = len(word)
                if length not in self.word_by_length:
                    self.word_by_length[length] = []
                self.word_by_length[length].append(word)

        print(f"Loaded {len(self.word_list)} words")

    def get_random_word(self, difficulty='medium', word_length=5):
        """
        Select a random word based on difficulty level and word length

        Parameters: difficulty (str): 'easy', 'medium', or 'hard'
                    word_length (int): Length of the word to select

        Returns: str: A word of the specified length and difficulty
        """
        if word_length in self.word_by_length and self.word_by_length[word_length]:
            available_words = self.word_by_length[word_length]
        else:
            available_words = self.word_list
        diff_params = self.difficulty_mapping.get(difficulty, self.difficulty_mapping['medium'])

        # Filter words by difficulty criteria
        suitable_words = []
        for word in available_words:
            unique_letters = len(set(word))

            # frequency calculation
            common_letters = set("etaoinshrdlu")
            letter_commonality = sum(1 for letter in word if letter in common_letters) / len(word)

            # Check if the word difficult
            if (unique_letters <= diff_params['max_unique'] and
                    letter_commonality >= diff_params['min_freq']):
                suitable_words.append(word)
        if not suitable_words and available_words:
            return random.choice(available_words)
        return random.choice(suitable_words) if suitable_words else random.choice(self.word_list)

    def validate_word(self, guess):
        """Check if a word exists in the word bank"""
        return guess.lower() in self.word_set
