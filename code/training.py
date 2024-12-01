import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import BaseWidget, run, lookup
from imslib.audio import Audio
from imslib.mixer import Mixer
from imslib.wavegen import WaveGenerator
from imslib.wavesrc import WaveBuffer, WaveFile
# from imslib.noteseq import NoteSequencer
from imslib.synth import Synth
from imslib.clock import SimpleTempoMap, AudioScheduler
from imslib.gfxutil import topleft_label, CEllipse, CRectangle, CLabelRect
from functools import reduce

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window

from attack import Attack
from training_aud_ctrl import TrainingAudioController
from AttackDisplay import AttackDisplay, AttackBox
from training_display_components import GemDisplay, ButtonDisplay, NowbarDisplay, lane_w_margin, lane_h, btns, max_x, min_x, accuracy_window
from AttackDatabase import AttackDatabase

y_margin = 0.3 #distance from bottom of boxes to edge of screen

class TrainingWidget(BaseWidget):
    def __init__(self, attacks):
        super(TrainingWidget, self).__init__()
        # audio
        self.audio = Audio(2)
        self.synth = Synth()# create TempoMap, AudioScheduler
        self.tempo_map  = SimpleTempoMap(120)
        self.sched = AudioScheduler(self.tempo_map)

        # connect scheduler into audio system
        self.audio.set_generator(self.sched)
        self.sched.set_generator(self.synth)

        # change this to make the attacks not all just winter haha
        self.attacks = attacks

        ### each ATTACK gets an AUDIO CONTROL, GAME DISPLAY, PLAYER, and ATTACK DISPLAY
        self.audio_ctrl = [TrainingAudioController(self.synth, self.sched, attack) for attack in attacks]
        self.game_display = [GameDisplay(attack) for attack in attacks]
        self.player = [Player(attacks[i], self.audio_ctrl[i], self.game_display[i]) for i in range(len(attacks))]
        self.attack_box = AttackBox(attacks, True, y_marg=y_margin)
        self.canvas.add(self.attack_box)
        
        self.curr_attack_index = 0  # attack that is currently selected
        self.attack_box.select(self.curr_attack_index) # display attack as selected in the selector
        self.canvas.add(self.game_display[self.curr_attack_index]) # display current attack
        self.training = False
        self.attacks_trained = 1 # keep track of how many attacks trained, 1 by default

        self.info = topleft_label()
        self.add_widget(self.info)

    def on_key_down(self, keycode, modifiers):

        # only change selected attack if not actively training
        if not self.training and keycode[1] in ('right', 'left', 'up', 'down'):
            new_ind = self.attack_box.move(keycode[1], self.curr_attack_index)
            if new_ind != self.curr_attack_index:
                self.canvas.remove(self.game_display[self.curr_attack_index])
                self.curr_attack_index = new_ind
                self.canvas.add(self.game_display[self.curr_attack_index])

        # train the selected attack
        if keycode[1] == "spacebar" and not self.training:
            self.audio_ctrl[self.curr_attack_index].play()
            self.player[self.curr_attack_index].done = False

        # play a note 
        button_idx = lookup(keycode[1], btns, (0,1,2,3,4,5,6,7))
        if button_idx != None:
            # print('down', button_idx)
            self.player[self.curr_attack_index].on_button_down(button_idx)

    def on_key_up(self, keycode):
        # button up
        button_idx = lookup(keycode[1], btns, (0,1,2,3,4,5,6,7))
        if button_idx != None:
            # print('up', button_idx)
            self.player[self.curr_attack_index].on_button_up(button_idx)

    def scoring(self):
        # Get the training accuracy percentage
        training_percent = self.game_display[self.curr_attack_index].get_training_percent()

        # Check if the training is mastered
        if training_percent > 0.5 and not self.attacks[self.curr_attack_index].unlocked:
            self.attacks_trained += 1
            self.attacks[self.curr_attack_index].unlocked = True
            return

    # handle changing displayed elements when window size changes
    # This function should call GameDisplay.on_resize
    def on_resize(self, win_size):
        for gd in self.game_display:
            gd.on_resize(win_size)

    def on_update(self):
        self.audio.on_update() # used to be # self.audio_ctrl.on_update()
        # everyone uses audio's time now, which is in ticks instead of seconds
        now = self.audio_ctrl[self.curr_attack_index].get_tick()
        self.game_display[self.curr_attack_index].on_update(now)
        self.player[self.curr_attack_index].on_update(now)
        
        self.scoring()

        self.training = reduce(lambda tot,aud_ctrl: tot or aud_ctrl.training, self.audio_ctrl, False)

        self.info.text = 'p: pause/unpause song\n'
        self.info.text += f'song time: {now:.2f}\n'
        self.info.text += f'index {self.curr_attack_index}\n'
        self.info.text += f'attacks trained: {self.attacks_trained}\n'
        self.info.text += f'num objects: {self.game_display[self.curr_attack_index].get_num_object()}\n'
        self.info.text += f'accuracy of run: {self.game_display[self.curr_attack_index].acc}\n'
        self.info.text += f'training percent: {self.game_display[self.curr_attack_index].get_training_percent() * 100:.0f}%'

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
    def __init__(self, attack, audio_ctrl, display, defense=False):
        super(Player, self).__init__()

        self.gems = attack.gems
        self.attack = attack
        self.idx = 0
        self.defense = defense

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
        # print(lane, target_lane)
        # print(self.tick, target_time)
        if target_time - accuracy_window < self.tick:
            if self.defense or lane == target_lane:
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
    attacks = AttackDatabase().get_attack_roster(0)
    run(TrainingWidget(attacks))
