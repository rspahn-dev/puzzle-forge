"""Core word scramble generation — no external dependencies."""
import random


class ScrambledWord:
    def __init__(self, answer, scrambled):
        self.answer = answer
        self.scrambled = scrambled


class WordScramblePuzzle:
    def __init__(self, words, seed=None):
        self.words = [w.upper().strip() for w in words if w.strip()]
        self._rng = random.Random(seed)
        self.items = [ScrambledWord(word, self._scramble(word)) for word in self.words]

    def _scramble(self, word, attempts=20):
        letters = list(word)
        for _ in range(attempts):
            self._rng.shuffle(letters)
            scrambled = "".join(letters)
            if scrambled != word:
                return scrambled
        return scrambled

    def to_dict(self):
        return {
            "items": [{"scrambled": i.scrambled, "answer": i.answer, "length": len(i.answer)} for i in self.items],
        }

    def to_storage_dict(self):
        return {
            "items": [{"scrambled": i.scrambled, "answer": i.answer} for i in self.items],
        }

    @classmethod
    def from_items(cls, items):
        obj = cls.__new__(cls)
        obj.words = [i["answer"] for i in items]
        obj.items = [ScrambledWord(i["answer"], i["scrambled"]) for i in items]
        return obj
