from functools import reduce

# Attack wrapper
class Attack:
    def __init__(self, attack, metro_time, metro=[(480, 60)], unlocked=False):
        self.name = attack["name"]
        self.notes = attack["notes"]
        self.damage = attack["damage"]
        self.lanes = attack["lanes"] # what note each button corresponds to

        self.metro_time = metro_time
        self.metro = metro # default is one ping every 480 ticks

        self.unlocked = unlocked

        self.song_time = reduce(lambda a,x: a+x[0], self.notes, 0)
        sd = [(duration, self.lanes.index(pitch)) for duration, pitch in self.notes]
        tot = metro_time
        gems = []
        for gem in sd:
            gems += [(tot, gem[1])]
            tot += gem[0]
        self.gems = gems

    def get_note(self, idx):
        return self.notes[idx]

    def last_note(self, idx):
        return idx == len(self.notes) - 1

    def unlock(self):
        self.unlocked = True

