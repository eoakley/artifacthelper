from itertools import chain
import pickle

class Artibuff_Card:
    def __init__(self, name, win_rate,pick_rate):
        self.name = name
        self.win_rate = win_rate
        self.pick_rate = pick_rate

    def __repr__(self):
        return 'WR: ' + str(self.win_rate)[:-1] + '% | PR: ' + str(self.pick_rate)[:-1] + '%'
    def __str__(self):
        return 'WR: ' + str(self.win_rate)[:-1] + '% | PR: ' + str(self.pick_rate)[:-1] + '%'
