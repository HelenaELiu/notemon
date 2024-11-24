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
from imslib.gfxutil import topleft_label, CEllipse, CRectangle, CLabelRect
from functools import reduce
from AttackDisplay import AttackDisplay
y_margin = 0.3 #distance from bottom of boxes to edge of screen

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window

from noteseq2 import NoteSequencer2
from attack import Attack

# buttons we use for notes
btns = "asdfjkl;"

# UI settings
lane_h = 0.8       # height of lane
btn_h = 0.2        # height of btns from the bottom of screen (as proportion of window height)
lane_w_margin = 0.1
space_betw_btns = 0.1
accuracy_window = 100 # num seconds window
button_width = 0.9 # fraction of the space betw lines
nowbar_h = 0.1

# song data: make into a class?
winter_metro_time = 480 * 4
winter_notes = ((240, 60), (240, 72), (240, 67), (240, 63), 
          (240, 60), (240, 72), (240, 67), (240, 63), (240, 60),)
# song_time = reduce(lambda a,x: a+x[0], winter, 0)
winter_lanes = (60, 62, 63, 65, 67, 69, 71, 72) # can change; should change for every song?
# metro = ((480, 60),)

winter_attack = Attack(winter_notes, winter_metro_time, winter_lanes)

# for dynamic nowbar on lane
max_x = (1 - lane_w_margin)
min_x = lane_w_margin

class TrainingWidget(BaseWidget):
    def __init__(self):
        super(TrainingWidget, self).__init__()

        print('hi')
        # audio
        self.audio = Audio(2)
        self.synth = Synth()# create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        ### each ATTACK gets an AUDIO CONTROL, GAME DISPLAY, and PLAYER
        # audio control
        self.audio_ctrl = AudioController(self.synth, self.sched, winter_attack)
        # game display
        self.game_display = GameDisplay(winter_attack)
        self.canvas.add(self.game_display)
        # player needs the above
        self.player = Player(winter_attack, self.audio_ctrl, self.game_display)

        self.info = topleft_label()
        self.add_widget(self.info)

    def on_key_down(self, keycode, modifiers):
        # play / pause toggle
        if keycode[1] == 'p':
            if not self.audio_ctrl.training:
                self.audio_ctrl.play()
                self.player.done = False

        # button down
        button_idx = lookup(keycode[1], btns, (0,1,2,3,4,5,6,7))
        if button_idx != None:
            # print('down', button_idx)
            self.player.on_button_down(button_idx)

    def on_key_up(self, keycode):
        # button up
        button_idx = lookup(keycode[1], btns, (0,1,2,3,4,5,6,7))
        if button_idx != None:
            # print('up', button_idx)
            self.player.on_button_up(button_idx)

    # handle changing displayed elements when window size changes
    # This function should call GameDisplay.on_resize
    def on_resize(self, win_size):
        self.game_display.on_resize(win_size)

    def on_update(self):
        self.audio.on_update() # used to be # self.audio_ctrl.on_update()
        # everyone uses audio's time now, which is in ticks instead of seconds
        now = self.audio_ctrl.get_tick()
        self.game_display.on_update(now)
        self.player.on_update(now)

        self.info.text = 'p: pause/unpause song\n'
        self.info.text += f'song time: {now:.2f}\n'
        self.info.text += f'num objects: {self.game_display.get_num_object()}\n'
        self.info.text += f'accuracy of run: {self.game_display.acc}\n'
        self.info.text += f'training percent: {self.game_display.get_training_percent():.2f}'

class AudioController(object):
    def __init__(self, synth, sched, attack):
        super(AudioController, self).__init__()
        self.synth = synth
        self.sched = sched
        self.metro_time = attack.metro_time

        self.solo = NoteSequencer2(self.sched, self.synth, 0, (0,88), attack.notes, False, wait=attack.metro_time)
        self.metro = NoteSequencer2(self.sched, self.synth, 1, (128, 0), attack.metro, True, wait=0)
        self.total_solo_time = attack.song_time

        # start ready
        self.training = False
        self.player = False
        self.song_start_tick = -10000 # so that we never see the nowbar move when we don't want it to

    # start / stop the song
    def play(self):
        print('hi')
        curr_tick = self.sched.get_tick()

        self.metro.start()
        self.solo.start()
        next_beat = quantize_tick_up(curr_tick, kTicksPerQuarter) # this is when the above noteseqs start
        # self.sched.post_at_tick(self._play_song, next_beat)
        self.song_start_tick = next_beat
        self.training = True

        # pause metronome for a little bit before starting player's turn
        self.sched.post_at_tick(self._stop_metro, next_beat + self.metro_time + self.total_solo_time)

        # start metro again so player knows beat
        player_start = next_beat + self.metro_time + self.total_solo_time + 480
        self.sched.post_at_tick(self._player_turn, player_start)

    # def _play_song(self, tick):
    #     print('playing', tick)
    #     self.metro.start()
    #     self.solo.start()
    #     self.song_start_tick = tick

    def _stop_metro(self, tick):
        self.metro.stop()

    def _player_turn(self, tick):
        self.metro.start()
        self.player = True # now the player will playing
        self.song_start_tick = quantize_tick_up(tick, kTicksPerQuarter) # this is when the above metro will start
        self.sched.post_at_tick(self._set_to_normal, self.song_start_tick + self.metro_time + self.total_solo_time) # afterwards, reset everything

    def _set_to_normal(self, tick):
        self.metro.stop()
        self.training = False
        self.player = False
        self.song_start_tick = -10000 # so that we never see the nowbar move when we don't want it to

    # return current time (in ticks) of song
    def get_tick(self):
        return self.sched.get_tick() - self.song_start_tick

class ButtonDisplay(InstructionGroup):
    def __init__(self, lane, color):
        super(ButtonDisplay, self).__init__()

        self.lane = lane
        self.x = Window.width // 2 + Window.width * space_betw_btns * (-3.5 + lane)

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
        self.color.hsv = (1/8 * self.lane,1,1)

    # back to normal state
    def on_up(self):
        self.color.hsv = (1/8 * self.lane,0.9,0.5)

    # modify object positions based on new window size
    def on_resize(self, win_size):
        self.x = win_size[0] // 2 + win_size[0] * space_betw_btns * (-3.5 + self.lane)
        size = space_betw_btns * win_size[0] * button_width
        self.button.csize = (size, size)
        self.button.cpos=(self.x, btn_h * win_size[1])
        self.label.cpos = (self.x, btn_h * win_size[1])

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
    def __init__(self, lane, time, color, tick_to_xpos, attack):
        super(GemDisplay, self).__init__()

        self.lane = lane
        self.time = time
        self.tick_to_xpos = tick_to_xpos
        self.song_time = attack.song_time
        self.metro_time = attack.metro_time

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

# Displays all game elements: nowbar, buttons, downbeats, gems
class GameDisplay(InstructionGroup):
    def __init__(self, attack):
        super(GameDisplay, self).__init__()

        self.acc = 0
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
        self.gems = [GemDisplay(lane, time, (1/8 * (lane),1,1), self.tick_to_xpos, attack) for time,lane in attack.gems]

        # buttons
        self.buttons = [ButtonDisplay(i, (1/8 * i,0.9,0.5)) for i in range(8)]
        for button in self.buttons:
            self.add(button)

        # commands
        self.add(Color(hsv=[1,0,1]))
        self.listen = CLabelRect((Window.width//2, Window.height//2), "Listen!")
        self.play = CLabelRect((Window.width//2, Window.height//2), "Play!")

    def tick_to_xpos(self, tick):
        # TODO write this
        maxx = Window.width * max_x
        minx = Window.width * min_x
        return tick * (maxx - minx) / (self.attack.song_time + self.attack.metro_time) + minx

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

class Player(object):
    def __init__(self, attack, audio_ctrl, display):
        super(Player, self).__init__()

        self.gems = attack.gems
        self.attack = attack
        self.idx = 0
        # self.lanes = {}

        self.display = display
        self.audio_ctrl = audio_ctrl
        self.tick = 0
        self.done = False

        self.acc = 0

        self.listening = False
        self.playing = False

    # called by MainWidget
    def on_button_down(self, lane):
        # self.lanes.add(lane)
        self.display.on_button_down(lane)
        self.audio_ctrl.synth.noteon(2, self.attack.lanes[lane], 100)
        if self.done or not self.audio_ctrl.player:
            return
        

        target_time = self.gems[self.idx][0]
        target_lane = self.gems[self.idx][1]
        print(lane, target_lane)
        print(self.tick, target_time)
        if target_time - accuracy_window < self.tick:
            if lane == target_lane:
                self.display.gem_hit(self.idx)
                self.acc += 1
                self.display.set_acc(self.acc)
                # only do this if gem hits. 
                if self.idx < len(self.gems) - 1:
                    self.idx += 1
                else:
                    self.done = True
                    self.idx = 0

                return
        
        # if you hit an unneccesary note:
            self.acc -= 1
            self.display.set_acc(self.acc)

    # called by MainWidget
    def on_button_up(self, lane):
        # self.lanes.remove(lane)
        self.display.on_button_up(lane)
        self.audio_ctrl.synth.noteoff(2, self.attack.lanes[lane])

    # needed to check for pass gems (ie, went past the slop window)
    def on_update(self, tick):
        if not self.listening and not self.playing and self.audio_ctrl.training:
            self.acc = 0
            self.display.set_acc(self.acc)
            self.listening = True
            self.display.listen_command()

        if not self.playing and self.audio_ctrl.player:
            self.playing = True
            self.listening = False
            self.display.play_command()

        if self.playing and not self.audio_ctrl.training:
            self.playing = False
            self.display.remove_play_command()

        self.tick = tick
        if self.done or not self.audio_ctrl.player:
            return

        if self.gems[self.idx][0] + accuracy_window < tick:
            self.display.gem_pass(self.idx)
            self.acc -= 1
            self.display.set_acc(self.acc)
            
            if self.idx < len(self.gems) - 1:
                self.idx += 1
            else:
                self.done = True
                self.idx = 0

if __name__ == "__main__":
    run(TrainingWidget())