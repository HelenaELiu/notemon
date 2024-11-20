# Attack wrapper
class Attack:
    def __init__(self, notes):
        self.notes = notes

    def get_note(self, idx):
        return self.notes[idx]

    def last_note(self, idx):
        return idx == len(self.notes) - 1

