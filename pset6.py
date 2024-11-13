#####################################################################
#
# This software is to be used for MIT's class Interactive Music Systems only.
# Since this file may contain answers to homework problems, you MAY NOT release it publicly.
#
#####################################################################

import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import BaseWidget, run, lookup
from imslib.audio import Audio
from imslib.mixer import Mixer
from imslib.note import NoteGenerator, Envelope
from imslib.wavegen import WaveGenerator
from imslib.wavesrc import WaveBuffer, WaveFile
from imslib.gfxutil import topleft_label, resize_topleft_label, CLabelRect, KFAnim, AnimGroup
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window

from kivy.clock import Clock

from math import cos, sin, radians

# configuration parameters:
nowbar_h = 0.2        # height of nowbar from the bottom of screen (as proportion of window height)
nowbar_w_margin = 0.1 # margin on either side of the nowbar (as proportion of window width)
time_span = 2.0       # time (in seconds) that spans the full vertical height of the Window
beat_marker_len = 0.2 # horizontal length of beat marker (as a proportion of window width)

C_major_scale = [60, 62, 64, 65, 67, 69, 71, 72]
notes = {1: NoteGenerator(C_major_scale[1], 0.5, 'sine'), 1: NoteGenerator(C_major_scale[1], 0.5, 'sine'),
1: NoteGenerator(C_major_scale[1], 0.5, 'sine'), 1: NoteGenerator(C_major_scale[1], 0.5, 'sine'),
1: NoteGenerator(C_major_scale[1], 0.5, 'sine'), 1: NoteGenerator(C_major_scale[1], 0.5, 'sine'),
1: NoteGenerator(C_major_scale[1], 0.5, 'sine'), 1: NoteGenerator(C_major_scale[1], 0.5, 'sine'),}
# self.mixer.add(Envelope(notes[lane], 0.01, 1, 1, 1))


class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()

        song_base_name = 'MoreThanAFeeling'
        
        self.audio = Audio(1)
        self.mixer = Mixer()
        self.audio.set_generator(self.mixer)

        self.song_data = SongData(song_base_name)
        self.audio_ctrl = AudioController(song_base_name)
        self.display = GameDisplay(self.song_data)
        self.player = Player(self.song_data, self.audio_ctrl, self.display)

        self.canvas.add(self.display)
        
        self.info = topleft_label()

        x1 = Window.width * (nowbar_w_margin + 0.01)
        x2 = Window.width * (1- nowbar_w_margin - 0.01)
        dist = (x2 - x1)/7
        lane_to_pos = {1:x1, 2:x1 + dist, \
        3:x1 + 2*dist, 4:x1 + 3*dist, 5:x1 + 4*dist, 6:x1 + 5*dist, \
        7:x1 + 6*dist, 8:x1 + 7*dist}
        y = time_to_ypos(0)

        self.label1 = Label(text='A', font_size=50, color=(1, 1, 1, 1))  # White letter
        self.label1.center = (lane_to_pos[1], y)  # Position the label in the center of the triangle

        self.label2 = Label(text='S', font_size=50, color=(1, 1, 1, 1))  # White letter
        self.label2.center = (lane_to_pos[2], y)  # Position the label in the center of the triangle

        self.label3 = Label(text='D', font_size=50, color=(1, 1, 1, 1))  # White letter
        self.label3.center = (lane_to_pos[3], y)  # Position the label in the center of the triangle

        self.label4 = Label(text='F', font_size=50, color=(1, 1, 1, 1))  # White letter
        self.label4.center = (lane_to_pos[4], y)  # Position the label in the center of the triangle

        self.label5 = Label(text='J', font_size=50, color=(1, 1, 1, 1))  # White letter
        self.label5.center = (lane_to_pos[5], y)  # Position the label in the center of the triangle

        self.label6 = Label(text='K', font_size=50, color=(1, 1, 1, 1))  # White letter
        self.label6.center = (lane_to_pos[6], y)  # Position the label in the center of the triangle

        self.label7 = Label(text='L', font_size=50, color=(1, 1, 1, 1))  # White letter
        self.label7.center = (lane_to_pos[7], y)  # Position the label in the center of the triangle

        self.label8 = Label(text=';', font_size=50, color=(1, 1, 1, 1))  # White letter
        self.label8.center = (lane_to_pos[8], y)  # Position the label in the center of the triangle
                
        self.add_widget(self.label1)
        self.add_widget(self.label2)
        self.add_widget(self.label3)
        self.add_widget(self.label4)
        self.add_widget(self.label5)
        self.add_widget(self.label6)
        self.add_widget(self.label7)
        self.add_widget(self.label8)
        self.add_widget(self.info)

    def on_key_down(self, keycode, modifiers):
        # play / pause toggle
        if keycode[1] == 'p':
            self.audio_ctrl.toggle()

        # button down
        button_idx = lookup(keycode[1], 'asdfjkl;', (0,1,2,3,4,5,6,7))
        if button_idx != None:
            # print('down', button_idx)
            self.player.on_button_down(button_idx+1) # to adjust for lanes being from 1-5

    def on_key_up(self, keycode):
        # button up
        button_idx = lookup(keycode[1], 'asdfjkl;', (0,1,2,3,4,5,6,7))
        if button_idx != None:
            # print('up', button_idx)
            self.player.on_button_up(button_idx+1)

    # handle changing displayed elements when window size changes
    # This function should call GameDisplay.on_resize
    def on_resize(self, win_size):
        resize_topleft_label(self.info)
        self.display.on_resize(win_size)

    def on_update(self):
        self.audio.on_update()
        self.audio_ctrl.on_update()

        now = self.audio_ctrl.get_time()
        self.display.on_update(now)
        self.player.on_update(now)

        self.info.text = 'p: pause/unpause song\n'
        self.info.text += f'song time: {now:.2f}\n'
        self.info.text += f'score: {self.display.score}\n'

# Handles everything about Audio.
#   creates the main Audio object
#   load and plays solo and bg audio tracks
#   creates audio buffers for sound-fx (miss sound)
#   functions as the clock (returns song time elapsed)
class AudioController(object):
    def __init__(self, song_path):
        super(AudioController, self).__init__()
        self.audio = Audio(2)
        self.mixer = Mixer()
        self.audio.set_generator(self.mixer)

        # song
        self.bg_track = WaveGenerator(WaveFile(song_path + "_bg.wav"))
        self.solo_track = WaveGenerator(WaveFile(song_path + "_solo.wav"))
        self.mixer.add(self.bg_track)
        self.mixer.add(self.solo_track)

        # start paused
        self.bg_track.pause()
        self.solo_track.pause()

    # start / stop the song
    def toggle(self):
        self.bg_track.play_toggle()
        self.solo_track.play_toggle()

    # mute / unmute the solo track
    def set_mute(self, mute):
        if mute is True:
            self.solo_track.set_gain(0)
        elif mute is False:
            self.solo_track.set_gain(1) # want track to continue playing just mute and unmute

    # play a sound-fx (miss sound)
    def play_miss(self):
        self.miss_sound = WaveGenerator(WaveFile("miss_sound.wav"))
        self.mixer.add(self.miss_sound)
        self.miss_sound.play()

    # return current time (in seconds) of song
    def get_time(self):
        return self.bg_track.frame / Audio.sample_rate

    # needed to update audio
    def on_update(self):
        self.audio.on_update()

# for parsing gem text file: return (time, lane) from a single line of text
def lane_from_line(line):
    time, lane = line.strip().split('\t')
    # lane_to_color_dict = {1: (0, 1, 1), \
    #     2: (1, 0, 0), 3: (1, 1, 0), \
    #     4: (1, 0, 1), 5: (1, 0.647, 0)}

    lane_to_color_dict = {
    1: (1, 0, 0),    # Red 
    2: (0, 1, 0),    # Green
    3: (0, 0, 1),    # Blue
    4: (1, 1, 0),    # Yellow
    5: (0, 1, 1),    # Cyan
    6: (1, 0, 1),    # Magenta
    7: (1, 1, 1),    # White
    8: (1, 0.647, 0) # Orange
    }
    return (int(lane), float(time), lane_to_color_dict[int(lane)])

def time_from_line(line):
    time, beat = line.strip().split('\t')
    return float(time)

# Holds data for gems and downbeats.
class SongData(object):
    def __init__(self, song_base):
        super(SongData, self).__init__()
        self.gem_beats = []
        self.downbeat = []

    # TODO: figure out how gem and downbeat data should be represented and accessed...
        gem_beats_file = song_base + '_solo_beats copy.txt'
        lines = open(gem_beats_file).readlines()
        self.gem_beats = [lane_from_line(l) for l in lines]

        downbeat_file = song_base + '_bg_beats copy.txt'
        lines = open(downbeat_file).readlines()
        self.downbeat = [time_from_line(l) for l in lines]

    def get_gem_beats(self):
        return self.gem_beats

    def get_downbeat(self):
        return self.downbeat

def draw_triangle(x, y, size):
    points = []
    # Define the points of the triangle
    points = [x-40, y-40, x+40, y-40, x, y+40, x-40, y-40]
    return points

# Display for a single gem at a position with a hue or color
class GemDisplay(InstructionGroup):
    def __init__(self, lane, time, color):
        super(GemDisplay, self).__init__()

        self.lane = lane
        self.time = time
        self.color = Color(*color)

        self.gem = Line(width=1)
        self.gem_lowest_y_value = 0
        self.hit = False
        self.on_screen = False

        self.add(self.color)
        self.add(self.gem)
        
        self.color_appear_anim = KFAnim((self.time-1, 0), (self.time, 1))

    # change to display this gem being hit
    def on_hit(self):
        if self.hit:
            return # gem has already been hit
        self.hit = True # mark as hit
        self.remove(self.gem) 

    # change to display a passed or missed gem
    def on_pass(self):
        self.hit = True

    def on_resize(self, win_size):
        self._resize(win_size)
    
    def _resize(self, win_size):
        x1 = win_size[0] * (nowbar_w_margin + 0.01)
        x2 = win_size[0] * (1- nowbar_w_margin - 0.01)
        dist = (x2 - x1)/7
        lane_to_pos = {1:x1, 2:x1 + dist, \
        3:x1 + 2*dist, 4:x1 + 3*dist, 5:x1 + 4*dist, 6:x1 + 5*dist, \
        7:x1 + 6*dist, 8:x1 + 7*dist}
        x = lane_to_pos[self.lane]
        self.gem.points = draw_triangle(x,self.y, win_size[0]/32)
        self.gem_lowest_y_value = self.gem.points[1]
        
    # animate gem (position and animation) based on current time
    def on_update(self, now_time):

        x1 = Window.width * (nowbar_w_margin + 0.01)
        x2 = Window.width * (1- nowbar_w_margin - 0.01)
        dist = (x2 - x1)/7
        lane_to_pos = {1:x1, 2:x1 + dist, \
        3:x1 + 2*dist, 4:x1 + 3*dist, 5:x1 + 4*dist, 6:x1 + 5*dist, \
        7:x1 + 6*dist, 8:x1 + 7*dist}

        # x = lane_to_pos[self.lane]
        # self.y = time_to_ypos(self.time - now_time)

        # x1 = Window.width * nowbar_w_margin
        # x2 = Window.width * (1- nowbar_w_margin)
        # dist = x2 - x1
        # x = time_to_ypos(now_time - self.time)
        x = lane_to_pos[self.lane]
        self.y = (Window.height*0.8)+25

        self.color.a = self.color_appear_anim.eval(now_time)
        if now_time > self.time + 10:
            x = time_to_ypos(now_time - self.time)
        # self.color.a = self.color_disappear_anim.eval(now_time)

        self.gem.points = draw_triangle(x,self.y, Window.width/32)
        self.gem_lowest_y_value = self.gem.points[1]
        # return if it is visible:
        if 0 < self.gem_lowest_y_value < Window.height:
            self.on_screen = True
        else:
            self.on_screen = False
        return 0 < self.gem_lowest_y_value < Window.height 


# Displays the location of a downbeat in the song
class DownbeatDisplay(InstructionGroup):
    def __init__(self, time):
        super(DownbeatDisplay, self).__init__()

        self.time = time
        self.color = Color(hsv=(.1, .8, 1))
        self.line = Line(width=3)

        self.add(self.color)
        self.add(self.line)

    # animate the position based on current time
    def on_update(self, now_time):

        x1 = Window.width * (nowbar_w_margin + 0.01)
        x2 = Window.width * (1- nowbar_w_margin - 0.01)
        y = time_to_ypos(now_time - self.time)

        self.line.points = [y, (Window.height*0.8)-50, y, (Window.height*0.8)+50]

        x1 = Window.width * nowbar_w_margin
        x2 = Window.width * (1- nowbar_w_margin)

        # return if it is visible:
        return x1 < y < x2


# Displays one button on the nowbar
class ButtonDisplay(InstructionGroup):
    def __init__(self, lane, color):
        super(ButtonDisplay, self).__init__()
        self.lane = lane
        self.color = Color(*color)

        self.button = Line(width=1)

        self.add(self.color)
        self.add(self.button)

    # displays when button is pressed down
    def on_down(self):
        self.button.width = 10

    # back to normal state
    def on_up(self):
        self.button.width = 1

    # modify object positions based on new window size
    def on_resize(self, win_size):
        x1 = win_size[0] * (nowbar_w_margin + 0.01)
        x2 = win_size[0] * (1- nowbar_w_margin - 0.01)
        dist = (x2 - x1)/7
        lane_to_pos = {1:x1, 2:x1 + dist, \
        3:x1 + 2*dist, 4:x1 + 3*dist, 5:x1 + 4*dist, 6:x1 + 5*dist, \
        7:x1 + 6*dist, 8:x1 + 7*dist}
        x = lane_to_pos[self.lane]
        y = time_to_ypos(0)
        self.button.points = draw_triangle(x,y, win_size[0]/32)

def time_to_ypos(time):
    y_nowbar = Window.width * nowbar_w_margin
    m = Window.width / time_span
    y = m * time + y_nowbar
    return y

# Displays all game elements: nowbar, buttons, downbeats, gems
class GameDisplay(InstructionGroup):
    def __init__(self, song_data):
        super(GameDisplay, self).__init__()
        self.gem_data = song_data.get_gem_beats()
        self.downbeat_data = song_data.get_downbeat()

        self.gems = [GemDisplay(*g) for g in self.gem_data]
        for g in self.gems:
            self.add(g)

        self.downbeats = [DownbeatDisplay(d) for d in self.downbeat_data]
        for d in self.downbeats:
            self.add(d)
        
        lane_to_color_dict = {
            1: (1, 0, 0),    # Red
            2: (0, 1, 0),    # Green
            3: (0, 0, 1),    # Blue
            4: (1, 1, 0),    # Yellow
            5: (0, 1, 1),    # Cyan
            6: (1, 0, 1),    # Magenta
            7: (1, 1, 1),    # White
            8: (1, 0.647, 0) # Orange
            }

        self.button_data = [(1, lane_to_color_dict[1]), (2, lane_to_color_dict[2]), \
        (3, lane_to_color_dict[3]), (4, lane_to_color_dict[4]), (5, lane_to_color_dict[5]), \
        (6, lane_to_color_dict[6]), (7, lane_to_color_dict[7]), (8, lane_to_color_dict[8])]
        self.buttons = [ButtonDisplay(*b) for b in self.button_data]
        for b in self.buttons:
            self.add(b)
            b.on_resize(Window.size)

        self.nowbar = Line(width=3) # position of nowbar set in _resize()
        self.sidebar1 = Line(width=3)
        self.sidebar2 = Line(width=3)
        self.add(Color(1,1,1))
        self.add(self.nowbar)
        self.add(self.sidebar1)
        self.add(self.sidebar2)
        self._resize(Window.size)
        self.original_color = (0, 0, 0)
        self.score = 0

    # called by Player when succeeded in hitting this gem.
    def gem_hit(self, gem_idx):
        gem = self.gems[gem_idx]
        original_color = gem.color.rgb
        # gem shows it was hit by turning big and green
        gem.on_hit()
        for g in self.gems:
            if g.lane == gem.lane:
                g.color.rgb = (0,1,0)
                g.gem.width = 10
        Clock.schedule_once(lambda dt: self.reset_gem_colors(gem.lane, original_color), 0.5)

    def reset_gem_colors(self, lane, original_color):
        for g in self.gems:
            if g.lane == lane:
                g.color.rgb = original_color  # Reset to original color
                g.gem.width = 1
    
    # called by Player on pass or miss.
    def gem_pass(self, gem_idx):
        gem = self.gems[gem_idx]
        gem.on_pass()
        # gem.color.rgb = (0.5, 0.5, 0.5)

    # called by Player on button down
    def on_button_down(self, lane):
        for button in self.buttons:
            if button.lane == lane:
                button.on_down()

    # called by Player on button up
    def on_button_up(self, lane):
        for button in self.buttons:
            if button.lane == lane:
                button.on_up()

    # called by Player to update score
    def set_score(self, score):
        self.score = score

    # for when the window size changes
    def on_resize(self, win_size):
        self._resize(win_size)
        for b in self.buttons:
            b.on_resize(win_size)

    def _resize(self, win_size):
        # resize the nowbar
        x1 = win_size[0] * nowbar_w_margin
        x2 = win_size[0] * (1- nowbar_w_margin)
        y = time_to_ypos(0)
        self.nowbar.points = [x1, win_size[1]*0.8, x2, win_size[1]*0.8]
        self.sidebar1.points = [x1, (win_size[1]*0.8)+50, x1, (win_size[1]*0.8)-50]
        self.sidebar2.points = [x2, (win_size[1]*0.8)+50, x2, (win_size[1]*0.8)-50]

    def get_num_object(self):
        return len(self.children)

    # call every frame to handle animation needs
    def on_update(self, now_time):
        for g in self.gems:
            vis = g.on_update(now_time)
            in_list = g in self.children
            if vis and not in_list: 
                self.add(g)
            if not vis and in_list:
                self.remove(g)
            # if vis:
            #     g.color.a = g.color_anim.eval(now_time)
        
        for d in self.downbeats:
            vis = d.on_update(now_time)
            in_list = d in self.children
            if vis and not in_list:
                self.add(d)
            if not vis and in_list:
                self.remove(d)


# Handles game logic and keeps track of score.
# Controls the GameDisplay and AudioCtrl based on what happens
class Player(object):
    def __init__(self, song_data, audio_ctrl, display):
        super(Player, self).__init__()
        self.song_data = song_data
        self.audio_ctrl = audio_ctrl
        self.display = display
        self.gems = self.display.gems

        self.slop_window = 100  # +/- 100 ms
        self.hit = False
        self.lane_miss = False
        self.temporal_miss = False
        self.score = 0

    # called by MainWidget
    def on_button_down(self, lane):
        now = self.audio_ctrl.get_time()
        self.display.on_button_down(lane)
        current_time = now * 1000  # Convert to milliseconds
        
        for g in range(len(self.gems)):
            gem = self.gems[g]
            gem_time = gem.time * 1000  # gem.time is in seconds
            if gem_time - self.slop_window <= current_time <= gem_time + self.slop_window:
                if gem.lane == lane and gem.hit == False:
                    self.hit = True
                    self.display.gem_hit(g)
                    self.audio_ctrl.set_mute(False) # solo track unmutes
                    self.score += 1
                    self.display.set_score(self.score)
                else:
                    self.lane_miss = True  # Lane miss detected
                    self.display.gem_pass(g)
                    self.audio_ctrl.set_mute(True) # solo track mutes
                    self.audio_ctrl.play_miss()

        # Update the display based on the results
        if not self.hit and not self.lane_miss:
            self.temporal_miss = True
            self.audio_ctrl.set_mute(True) # solo track unmutes
            self.audio_ctrl.play_miss()

    # called by MainWidget
    def on_button_up(self, lane):
        self.display.on_button_up(lane)

    # needed to check for pass gems (ie, went past the slop window)
    def on_update(self, time):
        self.audio_ctrl.on_update()
        now = self.audio_ctrl.get_time()
        self.display.on_update(now)
        
        current_time = time * 1000  # Convert to milliseconds
        # Check for gems that have passed the NowBar and are no longer hittable
        for g in range(len(self.gems)):
            gem = self.gems[g]
            gem_time = gem.time * 1000  # Convert gem time to milliseconds
            if (current_time > gem_time + self.slop_window) and gem.on_screen and not gem.hit: # check gem.on_screen and gem.hit
                self.display.gem_pass(g)
                self.audio_ctrl.set_mute(True)


if __name__ == "__main__":
    run(MainWidget())

# fix resize of letters
# fix bar to be within right frame