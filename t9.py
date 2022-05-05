#!/usr/bin/env python3

import time
import sys
from getkey import getkey, keys

ERASE_LINE = "\x1b[2K"

# load dictionary
if len(sys.argv) != 2:
    print("usage: {} <dict.txt>".format(sys.argv[0]))
    sys.exit(1)

class T9Engine():
    T9 = {'.': 1, ',': 1, '!': 1, '?': 1,
          ':': 1, '-': 1, "'": 1,
          '(': 1, ')': 1, ';': 1,
          'a': 2, 'b': 2, 'c': 2,
          'd': 3, 'e': 3, 'f': 3,
          'g': 4, 'h': 4, 'i': 4,
          'j': 5, 'k': 5, 'l': 5,
          'm': 6, 'n': 6, 'o': 6,
          'p': 7, 'q': 7, 'r': 7, 's': 7,
          't': 8, 'u': 8, 'v': 8,
          'w': 9, 'x': 9, 'y': 9, 'z': 9}

    def __init__(self):
        self._lookup = {} # our dictionary
        self._cur = self._lookup # where we're sitting in the dictionary
        self._history = [] # breadcrumb pointers of the path we've taken through the dictionary
        self._completion_len = 0 # number of characters in the current completion state
        self._completion_choice = 0 # index into current 'words' array

    def load_dict(self, filename):
        with open(filename, "r") as dictionary:
            for word in dictionary.readlines():
                cur = self._lookup
                for c in word[:-1]:
                    num = self.T9[c.lower()]
                    if num not in cur:
                        cur[num] = {}
                    cur = cur[num]
                if "words" not in cur:
                    cur["words"] = []
                cur["words"].append(word[:-1])

    def add_digit(self, digit):
        if digit not in self._cur:
            return False
        self._completion_len += 1
        self._history.append(self._cur)
        self._cur = self._cur[digit]
        self._completion_choice = 0
        return self.get_completion()

    def backspace(self):
        self._completion_choice = 0
        if len(self._history) > 0:
            self._cur = self._history.pop()
            self._completion_len -= 1
        return self.get_completion()

    def get_completion(self):
        if self._completion_len == 0:
            return ""
        candidate = self._cur
        while candidate:
            if 'words' in candidate:
                return candidate['words'][self._completion_choice % len(candidate['words'])][:self._completion_len]
            for key in iter(candidate):
                if key != "words":
                    candidate = candidate[key]
                    break

    def next_completion(self):
        self._completion_choice += 1
        return self.get_completion()

    def new_completion(self):
        self._cur = self._lookup
        self._history.clear()
        self._completion_choice = 0
        self._completion_len = 0

    def get_cur_completion_len(self):
        return self._completion_len


t9_engine = T9Engine()

print("load...")
start = time.time()
t9_engine.load_dict(sys.argv[1])
print("loaded in {}s".format(time.time() - start))

line = ""
cur_word = ""

exit = False
doing_punctuation_stuff = False
while exit == False:
    key = getkey()

    if key == "Q":
        break

    # for using a-z and period instead of numbers
    if key.isalpha() or key == ".":
        key = str(T9Engine.T9[key.lower()])

    if key in "123456789":
        if key in "1":
            if not doing_punctuation_stuff:
                doing_punctuation_stuff = True
                t9_engine.new_completion()
                line += cur_word
                cur_word = ""
        tmp = t9_engine.add_digit(int(key))
        if tmp:
            cur_word = tmp
    elif key == keys.TAB:
        cur_word = t9_engine.next_completion()
    elif key == "0" or key == keys.SPACE:
        line += cur_word + " "
        cur_word = ""
        t9_engine.new_completion()
        doing_punctuation_stuff = False
    elif key == keys.BACKSPACE:
        if t9_engine.get_cur_completion_len() == 0:
            if len(line) == 0:
                continue
            line = line[:-1]
            words = line.split(" ")
            cur_word = words[-1]
            doing_punctuation_stuff = False
            for c in cur_word:
                if T9Engine.T9[c.lower()] == 1 and not doing_punctuation_stuff:
                    t9_engine.new_completion()
                    doing_punctuation_stuff = True
                t9_engine.add_digit(T9Engine.T9[c.lower()])
            if t9_engine.get_cur_completion_len() != 0:
                cur_word = line[-1*t9_engine.get_cur_completion_len():]
                line = line[:-1*t9_engine.get_cur_completion_len()]
        else:
            tmp = t9_engine.backspace()
            if tmp:
                cur_word = tmp
            else:
                cur_word = ''
    print(ERASE_LINE + "\r" + line + cur_word, end='')
