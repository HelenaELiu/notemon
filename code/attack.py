from functools import reduce
# from training_display_components import GemDisplay
from kivy.core.window import Window
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from imslib.gfxutil import CLabelRect
from training_display_components import GemDisplay, ButtonDisplay, NowbarDisplay, lane_w_margin, lane_h, max_x, min_x


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

        # self.gem_displays = [GemDisplay(lane, time, (1/8 * (lane),1,1), self.song_time, metro_time) for time,lane in gems]
        self.game_display = GameDisplay(gems, self.song_time, metro_time)

    def get_note(self, idx):
        return self.notes[idx]

    def last_note(self, idx):
        return idx == len(self.notes) - 1

    def unlock(self):
        self.unlocked = True

# Displays all game elements: nowbar, buttons, downbeats, gems
class GameDisplay(InstructionGroup):
    def __init__(self, gems, song_time, metro_time):
        super(GameDisplay, self).__init__()

        self.acc = 0
        self.gems_hit = 0
        self.song_time = song_time
        self.metro_time = metro_time
        # self.attack = attack

        # lane display
        self.add(Color(hsv=(1,0,0.2)))
        self.lane = Line(points=(lane_w_margin * Window.width, lane_h * Window.height, (1 - lane_w_margin) * Window.width, lane_h * Window.height), width=2)
        self.add(self.lane)

        # nowbar
        # self.add(Color(1,1,1))
        self.nowbar = NowbarDisplay(self.tick_to_xpos)
        self.add(self.nowbar)

        # gems
        # song data
        self.gems = [GemDisplay(lane, time, (1/8 * (lane),1,1), self.tick_to_xpos, self.song_time, metro_time) for time,lane in gems]

        # buttons
        self.buttons = [ButtonDisplay(i, (1/8 * i,0.9,0.5)) for i in range(8)]
        for button in self.buttons:
            self.add(button)

        # commands
        self.add(Color(hsv=[1,0,1]))
        self.listen = CLabelRect((Window.width//2, Window.height//2), "Listen!")
        self.play = CLabelRect((Window.width//2, Window.height//2), "Play!")

        self.attacks_trained = 0 # keep track of how many attacks trained, 1 by default

    def tick_to_xpos(self, tick):
        # TODO write this
        maxx = Window.width * max_x
        minx = Window.width * min_x
        return tick * (maxx - minx) / (self.song_time + self.metro_time) + minx

    # called by Player when succeeded in hitting this gem.
    def gem_hit(self, gem_idx):
        got = self.gems[gem_idx].on_hit()
        if got:
            self.gems_hit += 1

    def get_training_percent(self):
        return self.gems_hit / len(self.gems)

    # called by Player on pass or miss.
    def gem_pass(self, gem_idx):
        self.gems[gem_idx].on_pass()

    # called by Player on button down
    def on_button_down(self, lane):
        self.buttons[lane].on_down()

    # called by Player on button up
    def on_button_up(self, lane):
        self.buttons[lane].on_up()

    # called by Player to update accuracy (??)
    def set_acc(self, acc):
        self.acc = acc

    # command player to liten
    def listen_command(self):
        self.add(self.listen)

    # command player to play
    def play_command(self):
        self.remove(self.listen)
        self.add(self.play)

    # reset command
    def remove_play_command(self):
        self.remove(self.play)

    # for when the window size changes
    def on_resize(self, win_size):
        self.lane.points=(lane_w_margin * Window.width, lane_h * Window.height, (1 - lane_w_margin) * Window.width, lane_h * Window.height)
        for g in self.gems:
            g.on_resize(win_size)
        for button in self.buttons:
            button.on_resize(win_size)


    # call every frame to handle animation needs
    def on_update(self, now_tick):
        vis = self.nowbar.on_update(now_tick)
        if vis and self.nowbar not in self.children:
            self.add(self.nowbar)
        elif not vis and self.nowbar in self.children:
            self.remove(self.nowbar)

        # for b in self.beats:
        #     vis = b.on_update(now_time)

        #     # TODO write optimization code here
        #     if vis and b not in self.children:
        #         self.add(b)
        #     if not vis and b in self.children:
        #         self.remove(b)

        for g in self.gems:
            vis = g.on_update(now_tick)

            # TODO write optimization code here
            if vis and g not in self.children:
                self.add(g)
            if not vis and g in self.children:
                self.remove(g)

    # why do i keep this, i don't know
    def get_num_object(self):
        return len(self.children)