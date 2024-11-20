import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import BaseWidget, run, lookup
from imslib.audio import Audio
from imslib.mixer import Mixer
from imslib.wavegen import WaveGenerator
from imslib.wavesrc import WaveBuffer, WaveFile
# from imslib.noteseq import NoteSequencer
from imslib.synth import Synth
from imslib.clock import SimpleTempoMap, AudioScheduler, kTicksPerQuarter, quantize_tick_up
from imslib.gfxutil import topleft_label, CEllipse, CRectangle
from functools import reduce

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window

from noteseq2 import NoteSequencer2


lane_h = 0.8       # height of lane
btn_h = 0.2        # height of btns from the bottom of screen (as proportion of window height)
lane_w_margin = 0.1
# btn_w_margin = 0.1 # margin on either side of the btns (as proportion of window width)
space_betw_btns = 0.1
# time_span = 2.0       # time (in seconds) that spans the full vertical height of the Window
accuracy_window = 100 # num seconds window
button_width = 0.9 # of the space betw lines
nowbar_h = 0.1

max_x = Window.width * (1 - lane_w_margin)
min_x = Window.width * lane_w_margin

metro_time = 480 * 4
winter = ((240, 60), (240, 72), (240, 67), (240, 63), 
          (240, 60), (240, 72), (240, 67), (240, 63), (240, 60),)
song_time = reduce(lambda a,x: a+x[0], winter, 0)
lanes = (60, 62, 63, 65, 67, 69, 71, 72) # can change; should change for every song?
metro = ((480, 60),)


def tick_to_xpos(tick):
    # TODO write this
    return tick * (max_x - min_x) / (song_time + metro_time) + min_x

class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()

        print('hi')
        # audio
        self.audio_ctrl = AudioController()

        # song data
        sd = [(duration, lanes.index(pitch)) for duration, pitch in winter]
        tot = metro_time
        gems = []
        for gem in sd:
            gems += [(tot, gem[1])]
            tot += gem[0]

        # game display
        self.game_display = GameDisplay(gems)
        self.canvas.add(self.game_display)

        # player needs the above
        self.player = Player(gems, self.audio_ctrl, self.game_display)

        self.info = topleft_label()
        self.add_widget(self.info)

    def on_key_down(self, keycode, modifiers):
        # play / pause toggle
        if keycode[1] == 'p':
            if not self.audio_ctrl.training:
                self.audio_ctrl.play()
                self.player.done = False

        # button down
        button_idx = lookup(keycode[1], 'asdfjkl;', (0,1,2,3,4,5,6,7))
        if button_idx != None:
            # print('down', button_idx)
            self.player.on_button_down(button_idx)

    def on_key_up(self, keycode):
        # button up
        button_idx = lookup(keycode[1], 'asdfjkl;', (0,1,2,3,4,5,6,7))
        if button_idx != None:
            # print('up', button_idx)
            self.player.on_button_up(button_idx)

    # handle changing displayed elements when window size changes
    # This function should call GameDisplay.on_resize
    def on_resize(self, win_size):
        # self.game_display.on_resize(win_size)
        pass

    def on_update(self):
        self.audio_ctrl.on_update()
        # everyone uses audio's time now
        now = self.audio_ctrl.get_tick()
        self.game_display.on_update(now)
        self.player.on_update(now)

        self.info.text = 'p: pause/unpause song\n'
        self.info.text += f'song time: {now:.2f}\n'
        # self.info.text += f'num objects: {self.game_display.get_num_object()}\n'
        self.info.text += f'score: {self.player.score}'

class AudioController(object):
    def __init__(self):
        super(AudioController, self).__init__()
        self.audio = Audio(2)
        self.synth = Synth()
        # create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)
        self.mixer = Mixer()
        # self.audio.set_generator(self.mixer)

        # background
        # self.bg = WaveGenerator(WaveFile(song_path + " background.wav"))
        # self.mixer.add(self.bg)
        # self.solo = WaveGenerator(WaveFile(song_path + " solo.wav"))

        self.solo = NoteSequencer2(self.sched, self.synth, 0, (0,88), winter, False, wait=metro_time)
        self.metro = NoteSequencer2(self.sched, self.synth, 1, (128, 0), metro, True, wait=0)
        self.total_solo_time = song_time
        # self.mixer.add(self.solo)

        # start ready
        self.training = False
        self.player = False
        self.song_start_tick = -10000

    # start / stop the song
    def play(self):
        curr_tick = self.sched.get_tick()

        self.metro.start()
        self.solo.start()
        next_beat = quantize_tick_up(curr_tick, kTicksPerQuarter)
        # self.solo.start()
        # self.metro.start()
        self.sched.post_at_tick(self._play_song, next_beat)
        self.training = True
        self.sched.post_at_tick(self._stop_metro, next_beat + metro_time + self.total_solo_time)


        player_start = next_beat + metro_time + self.total_solo_time + 480
        self.sched.post_at_tick(self._player_turn, player_start)

    def _play_song(self, tick):
        print('playing', tick)
        self.metro.start()
        self.solo.start()
        self.song_start_tick = tick

    def _stop_metro(self, tick):
        self.metro.stop()

    def _player_turn(self, tick):
        print('hi')
        self.metro.start()
        print('player turn', tick)
        self.player = True
        self.song_start_tick = quantize_tick_up(tick, kTicksPerQuarter)
        print(self.song_start_tick, metro_time)
        self.sched.post_at_tick(self._set_to_normal, self.song_start_tick + metro_time + self.total_solo_time)

    def _set_to_normal(self, tick):
        self.metro.stop()
        self.training = False
        self.player = False
        print(tick - self.song_start_tick, metro_time + self.total_solo_time)
        self.song_start_tick = -10000
        print('normal', tick)

    # mute / unmute the solo track
    def set_mute(self, mute):
        if mute:
            self.solo.set_gain(0) # turn gain down
        else:
            self.solo.set_gain(1) # bring back to normal

    # play a sound-fx (miss sound)
    def play_miss(self):
        # add wacky sound to mixer
        # self.mixer.add(WaveGenerator(WaveFile("fail.wav")))
        pass

    # return current time (in seconds) of song
    def get_tick(self):
        # return self.solo.frame / Audio.sample_rate
        return self.sched.get_tick() - self.song_start_tick

    # needed to update audio
    def on_update(self):
        self.audio.on_update()

class ButtonDisplay(InstructionGroup):
    def __init__(self, lane, color):
        super(ButtonDisplay, self).__init__()

        self.lane = lane
        self.x = Window.width // 2 + Window.width * space_betw_btns * (-3.5 + lane)

        self.color = Color(hsv=color)
        self.add(self.color)
        size = space_betw_btns * Window.width * button_width
        # y_size = 0.1 * Window.height
        self.button = CEllipse(csize=(size, size), cpos=(self.x, btn_h * Window.height), segments=3)
        self.add(self.button)

    # displays when button is pressed down
    def on_down(self):
        self.color.hsv = (1/8 * self.lane,1,1)

    # back to normal state
    def on_up(self):
        self.color.hsv = (1/8 * self.lane,0.9,0.5)

    # modify object positions based on new window size
    def on_resize(self, win_size):
        self.x = win_size[0] // 2 + win_size[0] * space_betw_btns * (-2 + self.lane)
        size = space_betw_btns * win_size[0] * button_width
        # y_size = 0.1 * Window.height
        # y_size = accuracy_window * 2 / time_span * Window.height
        self.button.csize = (size, size)
        self.button.cpos=(self.x, btn_h * win_size[1])

class NowbarDisplay(InstructionGroup):
    def __init__(self):
        super(NowbarDisplay, self).__init__()

        self.color = Color(hsv=(.1, .8, 1)) # color of this beat line
        self.line = Line(width = 3) # line object to be drawn / animated in on_update()

        self.add(self.color)
        self.add(self.line)

    # animate the position based on current time
    def on_update(self, now_tick):
        x = tick_to_xpos(now_tick)
        self.line.points = (x, lane_h * Window.height - nowbar_h * Window.height / 2, x, lane_h * Window.height + nowbar_h * Window.height / 2)

        return x < max_x and x > min_x
    
class GemDisplay(InstructionGroup):
    def __init__(self, lane, time, color):
        super(GemDisplay, self).__init__()

        self.lane = lane
        self.time = time

        # center lanes around center of screen
        # self.x = (Window.width // 2) + Window.width * space_betw_lanes * (-2 + lane)
        self.x = tick_to_xpos(time)
        self.y = lane_h * Window.height

        self.true_hsv = color
        self.color = Color(hsv=(1,0,1))
        self.add(self.color)

        # diameter 1/2 of full space between lines
        # size = space_betw_lanes * Window.width * 0.5 * 0.5
        size = (max_x - min_x) / (song_time + metro_time) * accuracy_window

        self.gem = CEllipse(csize=(size, size), cpos=(self.x, self.y), segments=20)
        self.add(self.gem)

        self.hit = False
        # self.line = None

    # change to display this gem being hit
    def on_hit(self):
        # self.color.hsv = (1/5 * (self.lane),1,1)
        if not self.hit:
            self.color.hsv = self.true_hsv
            self.gem.segments = 3
            self.hit = True
        # self.add(Color(hsv=(1/5 * (self.lane),1,1), a=0.2))

        # this is short lived anyway but i guess should rescale
        # self.line = Line(points=(self.x, 0, self.x, Window.height), width=space_betw_lanes * button_width * 0.5 * 0.8 * Window.width)
        # self.add(self.line)

    # change to display a passed or missed gem
    def on_pass(self):
        if not self.hit:
            self.color.hsv = (1/8 * (self.lane),0.1,0.1)

    # animate gem (position and animation) based on current time
    def on_update(self, now_time):
        if now_time > (song_time + metro_time) and not self.hit:
            self.color.hsv = (1,0,1)
        return now_time > 0 and now_time <= (song_time + metro_time)
    
    def on_resize(self, win_size):
        self.y = lane_h * Window.height
        self.x = tick_to_xpos(self.time)
        self.gem.cpos = (self.x, self.y)

# Displays all game elements: nowbar, buttons, downbeats, gems
class GameDisplay(InstructionGroup):
    def __init__(self, gems):
        super(GameDisplay, self).__init__()

        # self.beat_times = song_data.beats
        # self.gem_times = song_data.gems
        self.score = 0

        # nowbar
        self.add(Color(1,1,1))
        self.nowbar = NowbarDisplay()
        self.add(self.nowbar)

        # gems
        self.gems = [GemDisplay(lane, time, (1/8 * (lane),1,1)) for time,lane in gems]

        # buttons
        self.buttons = [ButtonDisplay(i, (1/8 * i,0.9,0.5)) for i in range(8)]
        for button in self.buttons:
            self.add(button)

        # downbeats
        # self.beats = [DownbeatDisplay(time) for time in self.beat_times]

    # called by Player when succeeded in hitting this gem.
    def gem_hit(self, gem_idx):
        self.gems[gem_idx].on_hit()

    # called by Player on pass or miss.
    def gem_pass(self, gem_idx):
        self.gems[gem_idx].on_pass()

    # called by Player on button down
    def on_button_down(self, lane):
        self.buttons[lane].on_down()

    # called by Player on button up
    def on_button_up(self, lane):
        self.buttons[lane].on_up()

    # called by Player to update score
    def set_score(self, score):
        self.score = score

    # for when the window size changes
    def on_resize(self, win_size):
        for g in self.gems:
            g.on_resize(win_size)
        for button in self.buttons:
            button.on_resize(win_size)
        # self.nowbar.points=(nowbar_w_margin * Window.width, nowbar_h * Window.height, (1 - nowbar_w_margin) * Window.width, nowbar_h * Window.height)


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

            # if g not in self.children:
            #     print(vis, g.time - now_time)

        pass

    def get_num_object(self):
        return len(self.children)

class Player(object):
    def __init__(self, gems, audio_ctrl, display):
        super(Player, self).__init__()

        self.gems = gems
        print(gems)
        self.idx = 0
        # self.lanes = {}

        self.display = display
        self.audio_ctrl = audio_ctrl
        self.tick = 0
        self.done = False

        self.score = 0

    # called by MainWidget
    def on_button_down(self, lane):
        # self.lanes.add(lane)
        self.display.on_button_down(lane)
        self.audio_ctrl.synth.noteon(2, lanes[lane], 100)
        if self.done or not self.audio_ctrl.player:
            return
        

        target_time = self.gems[self.idx][0]
        target_lane = self.gems[self.idx][1]
        print(lane, target_lane)
        print(self.tick, target_time)
        if target_time - accuracy_window < self.tick:
            if lane == target_lane:
                self.display.gem_hit(self.idx)
                self.score += 1
                # self.display.set_score(self.score)
            # else: # not necessary for us, i think
                # self.audio_ctrl.play_miss()
                # self.audio_ctrl.set_mute(True)
                # self.display.gem_pass(self.idx)
            # only do this if gem hits. we probably want some other way of disincentivizing unnecessary wrong notes
                if self.idx < len(self.gems) - 1:
                    self.idx += 1
                else:
                    self.done = True
                    self.idx = 0
                # return # do you return? maybe you just want them to play it? maybe you want a noteseq to play it right?
        # else: 
            # self.audio_ctrl.play_miss()
            # self.audio_ctrl.set_mute(True)
            # pass

    # called by MainWidget
    def on_button_up(self, lane):
        # self.lanes.remove(lane)
        self.display.on_button_up(lane)
        self.audio_ctrl.synth.noteoff(2, lanes[lane])

    # needed to check for pass gems (ie, went past the slop window)
    def on_update(self, tick):
        self.tick = tick
        if self.done or not self.audio_ctrl.player:
            return

        if self.gems[self.idx][0] + accuracy_window < tick:
            self.display.gem_pass(self.idx)
            # self.audio_ctrl.set_mute(True)
            if self.idx < len(self.gems) - 1:
                self.idx += 1
            else:
                self.done = True
                self.idx = 0

if __name__ == "__main__":
    run(MainWidget())