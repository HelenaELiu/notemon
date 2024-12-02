from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from imslib.gfxutil import CEllipse, CRectangle, CLabelRect
from kivy.core.window import Window
from training_display_components import GemDisplay, NowbarDisplay, nowbar_h, btn_h

accuracy_window=100
lane_h = .4
lane_w_margin = 1/8
max_x = (1 - lane_w_margin)
min_x = lane_w_margin

class GemDisplay(InstructionGroup):
    def __init__(self, time, tick_to_xpos, attack):
        super(GemDisplay, self).__init__()

        self.time = time
        self.tick_to_xpos = tick_to_xpos
        self.song_time = attack.song_time
        self.metro_time = attack.metro_time

        self.x = tick_to_xpos(time)
        self.y = lane_h * Window.height

        self.hit_hsv = (.6, 1, 1)
        self.color = Color(hsv=(1,0,1))
        self.add(self.color)

        # diameter depending on accuracy window so they can see visually when to hit
        size = Window.width * (max_x - min_x) / (self.song_time + self.metro_time) * accuracy_window

        self.gem = CEllipse(csize=(size, size), cpos=(self.x, self.y), segments=20)
        self.add(self.gem)

        # hit gem stays hit; only need to unlock once
        self.hit = False

    # change to display this gem being hit
    def on_hit(self):
        # TODO add animation
        self.color.hsv = self.hit_hsv
        self.hit = True
            
    # change to display a passed or missed gem
    def on_pass(self):
        self.color.hsv = (0.1,0.1,0.1)

    # animate gem (position and animation) based on current time
    def on_update(self, now_time):
        # reset color after the song in case it is not hit
        if now_time > (self.song_time + self.metro_time):
            self.color.hsv = (1,0,1)
        return now_time > 0 and now_time <= (self.song_time + self.metro_time)
    
    def on_resize(self, win_size):
        self.y = lane_h * Window.height
        self.x = self.tick_to_xpos(self.time)
        size = Window.width * (max_x - min_x) / (self.song_time + self.metro_time) * accuracy_window
        self.gem.cpos = (self.x, self.y)
        self.gem.csize = (size, size)

class NowbarDisplay(InstructionGroup):
    def __init__(self, tick_to_xpos):
        super(NowbarDisplay, self).__init__()

        self.color = Color(hsv=(.1, .8, 1)) # color of nowbar
        self.line = Line(width = 3) # line object to be drawn / animated in on_update()
        self.tick_to_xpos = tick_to_xpos

        self.add(self.color)
        self.add(self.line)

    # animate the position based on current time
    def on_update(self, now_tick):
        x = self.tick_to_xpos(now_tick)
        self.line.points = (x, lane_h * Window.height - nowbar_h * Window.height / 2, x, lane_h * Window.height + nowbar_h * Window.height / 2)

        return x <= max_x * Window.width and x >= min_x * Window.width

class ButtonDisplay(InstructionGroup):
    def __init__(self):
        super(ButtonDisplay, self).__init__()

        self.x = Window.width // 2
        self.width = Window.width // 3
        self.height = Window.height // 5

        self.hsv = (.62, .9, .5) # CAN CHANGE
        self.color = Color(hsv=self.hsv)
        self.add(self.color)
        self.button = CRectangle(csize=(self.width, self.height), cpos=(self.x, btn_h * Window.height))
        self.add(self.button)

        self.add(Color(hsv=(1,0,1))) # label is white, don't really need to save bc it doesn't change
        self.label = CLabelRect(cpos=(self.x, btn_h * Window.height), text="Press space to block!")
        self.add(self.label)

    # displays when button is pressed down
    def on_down(self):
        self.color.hsv = (self.hsv[0], 1, 1)

    # back to normal state
    def on_up(self):
        self.color.hsv = self.hsv

    # modify object positions based on new window size
    def on_resize(self, win_size):
        self.x = Window.width // 2
        self.width = Window.width // 3
        self.height = Window.height // 5

        self.button.csize = (self.width, self.height)
        self.button.cpos=(self.x, btn_h * Window.height)
        self.label.cpos = (self.x, btn_h * Window.height)

class RhythmDisplay(InstructionGroup):
    def __init__(self, attack):
        super(RhythmDisplay, self).__init__()

        self.gems_hit = 0
        self.attack = attack

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
        self.gems = [GemDisplay(time, self.tick_to_xpos, attack) for time,lane in attack.gems]

        # buttons
        self.button = ButtonDisplay()
        self.add(self.button)

    def tick_to_xpos(self, tick):
        maxx = Window.width * max_x
        minx = Window.width * min_x
        return maxx - tick * (maxx - minx) / (self.attack.song_time + self.attack.metro_time) # BACKWARDS

    # called by Player when succeeded in hitting this gem.
    def gem_hit(self, gem_idx):
        self.gems_hit += 1
        self.gems[gem_idx].on_hit()

    def reset(self):
        gems_hit = self.gems_hit
        self.gems_hit = 0
        return gems_hit / len(self.gems)

    # called by Player on pass or miss.
    def gem_pass(self, gem_idx):
        self.gems[gem_idx].on_pass()

    # called by Player on button down
    def on_button_down(self):
        self.button.on_down()

    # called by Player on button up
    def on_button_up(self):
        self.button.on_up()

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

        for g in self.gems:
            vis = g.on_update(now_tick)

            # TODO write optimization code here
            if vis and g not in self.children:
                self.add(g)
            if not vis and g in self.children:
                self.remove(g)
