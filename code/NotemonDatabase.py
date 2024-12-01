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
        self.attacks = {"melored": ["winter", "magic flute", "rolling in the deep", "the feels"],
                        "meloyellow": ["fifth symphony", "fur elise", "hello", "shape of you"],
                        "melorange": ["fur elise", "rolling in the deep", "dynamite", "uptown funk"],
                        "melogreen": ["magic flute", "hello", "just the way you are", "uptown funk", "shape of you"],
                        "meloblue": ["hello", "espresso", "dynamite", "just the way you are"],
                        "melopurple": ["rolling in the deep", "uptown funk", "shape of you", "the feels"],}

#notemon_database = NotemonDatabase()