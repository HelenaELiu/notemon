from functools import reduce

# Attack wrapper
class Attack:
    def __init__(self, name, notes, metro_time, scale, metro=[(480, 60)], unlocked=False):
        self.name = name
        self.notes = notes
        self.metro_time = metro_time
        self.lanes = scale # what note each button corresponds to
        self.metro = metro # default is one ping every 480 ticks
        self.unlocked = unlocked

        self.song_time = reduce(lambda a,x: a+x[0], notes, 0)
        sd = [(duration, scale.index(pitch)) for duration, pitch in notes]
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

