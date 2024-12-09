from AttackDatabase import AttackDatabase

tot_num = 6

class NotemonDatabase(object):
    def __init__(self):
        #names
        self.attack_database = AttackDatabase()
        self.names = ["melored", "melorange", "meloyellow", "melogreen", "meloblue", "melopurple"]
        self.screen_names = ["Notemon_red", "Notemon_orange", "Notemon_yellow", "Notemon_green", "Notemon_blue", "Notemon_purple"]

        #image sources
        colors = ["red", "orange", "yellow", "green", "blue", "purple"]
        self.hs = [0/6, 1/6, 1/12, 2/6, 4/6, 5/6]
        self.img_srcs = []

        for color in colors:
            self.img_srcs.append("sprites/meloetta-" + color + ".png")

        #healths
        self.healths = {"melored": 100,
                        "melorange": 120,
                        "meloyellow": 140,
                        "melogreen": 160,
                        "meloblue": 180,
                        "melopurple": 200,}

        self.skills = {"melored": .3,
                        "melorange": .3,
                        "meloyellow": .4,
                        "melogreen": .3,
                        "meloblue": .3,
                        "melopurple": .4,}

        self.direction_enable = {"melored": False,
                        "melorange": False,
                        "meloyellow": False,
                        "melogreen": True,
                        "meloblue": True,
                        "melopurple": True,}

        #attacks
        self.attacks = {"melored": ["winter", "magic flute", "rolling in the deep", "the feels"],
                        "melorange": ["fifth symphony", "fur elise", "hello", "shape of you"],
                        "meloyellow": ["fur elise", "rolling in the deep", "dynamite", "uptown funk"],
                        "melogreen": ["magic flute", "hello", "just the way you are", "shape of you"],
                        "meloblue": ["hello", "espresso", "dynamite", "just the way you are"],
                        "melopurple": ["rolling in the deep", "uptown funk", "shape of you", "the feels"],}
        
    def make_notemon_array(self):
        return [Notemon(i, self) for i in range(6)]

class Notemon(object):
    def __init__(self, index, database):
        self.name = database.names[index]
        self.screen_name = database.screen_names[index]
        self.h = database.hs[index]
        self.img_src = database.img_srcs[index]
        self.health = database.healths[self.name]
        self.skill = database.skills[self.name]
        self.direction_enable = database.direction_enable[self.name]
        self.attacks = [database.attack_database.get_attack_from_name(attack_name, False) for attack_name in database.attacks[self.name]]
        self.attacks_trained = 0
        self.unlocked = False
#notemon_database = NotemonDatabase()
