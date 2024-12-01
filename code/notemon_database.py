class NotemonDatabase(object):
    def __init__(self):
        #names
        self.names = ["melored", "meloyellow", "melorange", "melogreen", "meloblue", "melopurple"]

        #image sources
        colors = ["red", "orange", "yellow", "green", "blue", "purple"]
        self.img_srcs = []

        for color in colors:
            self.img_srcs.append("sprites/meloetta-" + color + ".png")

        #healths
        self.healths = {"melored": 100,
                        "meloyellow": 120,
                        "melorange": 140,
                        "melogreen": 160,
                        "meloblue": 180,
                        "melopurple": 200,}

        #attacks
        self.attacks = {"melored": ["winter", "fifth symphony", "fur elise", "magic flute"],
                        "meloyellow": [],
                        "melorange": [],
                        "melogreen": [],
                        "meloblue": [],
                        "melopurple": [],}

#notemon_database = NotemonDatabase()