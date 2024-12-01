class AttackDatabase(object):
    def __init__(self):
        self.metro_time = 480 * 4
        
        self.names = ["winter", "fifth symphony", "fur elise", "magic flute"]

        self.keys = {
            'winter': (60, 'minor'),
            'fifth symphony' : (60, 'minor'),
            'fur elise': (64, 'minor'),
            'magic flute': (65, 'major'),
            }

        self.lanes = {
            'winter': (60, 62, 63, 65, 67, 69, 71, 72),
            'fifth symphony': (62, 63, 65, 67),
            'fur elise': (69, 71, 72, 74, 75, 76, 77, 79),
            'magic flute': (60, 62, 63, 65, 67, 69, 70, 72),
            }

        self.notes = {
            'winter': ((240, 60), (240, 72), (240, 67), (240, 63), 
                (240, 60), (240, 72), (240, 67), (240, 63), (240, 60),),
            'fifth symphony': ((240, 67), (240, 67), (240, 67), (240 * 5, 63), 
                (240, 65), (240, 65), (240, 65), (240 * 5, 62),),
            'fur elise': ((240, 76), (240, 75), (240, 76), (240, 75), 
                (240, 76), (240, 71), (240, 74), (240, 72), (240 * 2, 69),), 
            'magic flute': ((120, 69), (120, 67), (120, 69), (120, 70), 
                (240, 72), (240, 72), (240, 72), (240, 72), 
                (240, 72), (240, 72), (240, 72), (240, 72), (240 * 4, 65),),
            }