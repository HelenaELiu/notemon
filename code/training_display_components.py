from imslib.gfxutil import CEllipse, CRectangle, CLabelRect
from kivy.graphics.instructions import InstructionGroup
from kivy.core.window import Window
from kivy.graphics import Color, Line

# buttons we use for notes
btns = "asdfjkl;"

# UI settings
accuracy_window = 100 # num seconds window
button_width = 0.9 # fraction of the space betw lines
nowbar_h = 0.1
lane_h = 0.8       # height of lane
btn_h = 0.2        # height of btns from the bottom of screen (as proportion of window height)
lane_w_margin = 0.1
space_betw_btns = 0.1

# for dynamic nowbar on lane
max_x = (1 - lane_w_margin)
min_x = lane_w_margin

class ButtonDisplay(InstructionGroup):
    def __init__(self, lane, color, num_lanes=8):
        super(ButtonDisplay, self).__init__()

        self.lane = lane
        self.num_lanes = num_lanes
        self.x = Window.width // 2 + Window.width * space_betw_btns * (-(num_lanes - 1)/2 + lane)

        self.hsv = color
        self.color = Color(hsv=color)
        self.add(self.color)
        size = space_betw_btns * Window.width * button_width
        self.button = CEllipse(csize=(size, size), cpos=(self.x, btn_h * Window.height), segments=3)
        self.add(self.button)

        self.add(Color(hsv=(1,0,1))) # label is white, don't really need to save bc it doesn't change
        self.label = CLabelRect(cpos=(self.x, btn_h * Window.height), text=btns[lane])
        self.add(self.label)

    # displays when button is pressed down
    def on_down(self):
        if self.hsv[1] > 0:
            self.color.hsv = (self.hsv[0], 1, 1)
        else:
            self.color.hsv = (self.hsv[0], self.hsv[1], 1)

    # back to normal state
    def on_up(self):
        self.color.hsv = self.hsv

    # modify object positions based on new window size
    def on_resize(self, win_size):
        self.x = win_size[0] // 2 + win_size[0] * space_betw_btns * (-(self.num_lanes - 1)/2 + self.lane)
        size = space_betw_btns * win_size[0] * button_width
        self.button.csize = (size, size)
        self.button.cpos=(self.x, btn_h * win_size[1])
        self.remove(self.label)
        self.label = CLabelRect(cpos = (self.x, btn_h * win_size[1]), font_size=win_size[0]*0.013, text = btns[self.lane])
        self.add(self.label)

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
    
class GemDisplay(InstructionGroup):
    def __init__(self, lane, time, color, tick_to_xpos, song_time, metro_time):
        super(GemDisplay, self).__init__()

        self.lane = lane
        self.time = time
        self.tick_to_xpos = tick_to_xpos
        self.song_time = song_time
        self.metro_time = metro_time

        self.x = tick_to_xpos(time)
        self.y = lane_h * Window.height

        self.true_hsv = color
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
        if not self.hit:
            self.color.hsv = self.true_hsv
            self.gem.segments = 3
            self.hit = True
            return True
        self.color.hsv = (0.5, 1, 1)
        return False
            

    # change to display a passed or missed gem
    def on_pass(self):
        if not self.hit:
            self.color.hsv = (1/8 * (self.lane),0.1,0.1)

    # animate gem (position and animation) based on current time
    def on_update(self, now_time):
        # reset color after the song in case it is not hit
        if now_time > (self.song_time + self.metro_time):
            if not self.hit:
                self.color.hsv = (1,0,1)
            else:
                self.color.hsv = self.true_hsv
        return now_time > 0 and now_time <= (self.song_time + self.metro_time)
    
    def on_resize(self, win_size):
        self.y = lane_h * Window.height
        self.x = self.tick_to_xpos(self.time)
        size = Window.width * (max_x - min_x) / (self.song_time + self.metro_time) * accuracy_window
        self.gem.cpos = (self.x, self.y)
        self.gem.csize = (size, size)
