import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import BaseWidget, run, lookup
from imslib.audio import Audio
from imslib.mixer import Mixer
from imslib.wavegen import WaveGenerator
from imslib.wavesrc import WaveBuffer, WaveFile
from imslib.noteseq import NoteSequencer

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window
from imslib.gfxutil import topleft_label, resize_topleft_label, AnimGroup, KFAnim, CEllipse, CLabelRect
from imslib.clock import Clock, SimpleTempoMap, AudioScheduler, tick_str, kTicksPerQuarter, quantize_tick_up
from imslib.synth import Synth
import random

x_margin = 1/10 #distance from sides of boxes to edge of screen
y_margin = 1/20 #distance from bottom of boxes to edge of screen
box_width = 7/20 #width of boxes
box_height = 1/6 #height of boxes
radius_margin = 1/16 #radius of notemon circles


class MainWidget(BaseWidget):
    def __init__(self):
        super(MainWidget, self).__init__()
        self.display = GameDisplay()
        self.canvas.add(self.display)

        self.audio_ctrl = AudioController()
        self.player = Player(self.audio_ctrl, self.display)

        self.info = topleft_label()
        self.add_widget(self.info)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == "up":
            self.player.on_button_up()
        elif keycode[1] == "down":
            self.player.on_button_down()
        elif keycode[1] == "left":
            self.player.on_button_left()
        elif keycode[1] == "right":
            self.player.on_button_right()
        elif keycode[1] == "enter":
            self.player.on_button_enter()

    def on_update(self):
        self.player.on_update()

        self.info.text = 'Let\'s Battle!\n'


# Display for a single attack box
class AttackDisplay(InstructionGroup):
    def __init__(self, index, name, damage, show):
        super(AttackDisplay, self).__init__()
        self.audio = Audio(2)
        self.mixer = Mixer()
        self.audio.set_generator(self.mixer)

        self.index = index
        self.name = name
        self.damage = damage
        self.show = show

        #opponents attacks are not shown, only ours are
        if show:
            #graphics
            colors = [0.1, 0.5, 0.7, 0.85]
            self.color = Color(hsv=(colors[index], 1, 1))
            self.color.a = 0.7
            self.add(self.color)

            w = box_width * Window.width
            h = box_height * Window.height

            x1 = x_margin * Window.width
            y1 = 2 * y_margin * Window.width + h

            y2 = y_margin * Window.width
            x2 = (1 - x_margin) * Window.width - w

            if index == 0:
                self.box = Line(rectangle = (x1, y1, w, h), width = 3)
                self.label = CLabelRect(cpos = (x1 + w // 2, y1 + h // 2), text = name)
            elif index == 1:
                self.box = Line(rectangle = (x2, y1, w, h), width = 3)
                self.label = CLabelRect(cpos = (x2 + w // 2, y1 + h // 2), text = name)
            elif index == 2:
                self.box = Line(rectangle = (x1, y2, w, h), width = 3)
                self.label = CLabelRect(cpos = (x1 + w // 2, y2 + h // 2), text = name)
            elif index == 3:
                self.box = Line(rectangle = (x2, y2, w, h), width = 3)
                self.label = CLabelRect(cpos = (x2 + w // 2, y2 + h // 2), text = name)

            self.add(self.box)
            self.add(self.label)

    #when considering this box for selection, make outline brighter and larger
    def select(self):
        if self.show:
            self.color.a = 1
            self.box.width = 10

    #revert outline to normal
    def unselect(self):
        if self.show:
            self.color.a = 0.7
            self.box.width = 3


# Display for a single notemon sprite
class NotemonDisplay(InstructionGroup):
    def __init__(self, health, opponent):
        super(NotemonDisplay, self).__init__()

        self.health = health
        self.opponent = opponent
        self.fainted = False

        #graphics
        r = radius_margin * Window.width
        
        if opponent:
            self.color = Color(1, 0, 0)
            self.x = (1 - 2 * x_margin) * Window.width
            self.y = (1 - 3 * y_margin) * Window.height
        else:
            self.color = Color(0, 1, 0)
            self.x = 2 * x_margin * Window.width
            self.y = (1 - 6 * y_margin) * Window.height
        
        self.notemon = Line(circle = (self.x, self.y, r), width = 3)
        self.label = CLabelRect(cpos = (self.x, self.y), text = str(self.health))

        self.add(self.color)
        self.add(self.notemon)
        self.add(self.label)
    
    def take_damage(self, damage):
        if self.health - damage < 0:
            self.health = 0
            self.fainted = True
        else:
            self.health -= damage
    
    def on_update(self):
        self.remove(self.label)
        self.label = CLabelRect(cpos = (self.x, self.y), text = str(self.health))
        self.add(self.label)


winter = ((240, 60), (240, 72), (240, 67), (240, 63), 
          (240, 60), (240, 72), (240, 67), (240, 63), (240, 60),)
fifth_symphony = ((240, 67), (240, 67), (240, 67), (240 * 5, 63), 
                  (240, 65), (240, 65), (240, 65), (240 * 5, 62),)
fur_elise = ((240, 76), (240, 75), (240, 76), (240, 75), 
             (240, 76), (240, 71), (240, 74), (240, 72), (240 * 2, 69),)
magic_flute = ((120, 69), (120, 67), (120, 69), (120, 70), 
               (240, 72), (240, 72), (240, 72), (240, 72), 
               (240, 72), (240, 72), (240, 72), (240, 72), (240 * 4, 65),)


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

        #create song
        self.seqs = []

        self.seq1 = NoteSequencer(self.sched, self.synth, 1, (0,88), winter, False)
        self.seqs.append(self.seq1)

        self.seq2 = NoteSequencer(self.sched, self.synth, 1, (0,88), fifth_symphony, False)
        self.seqs.append(self.seq2)

        self.seq3 = NoteSequencer(self.sched, self.synth, 1, (0,88), fur_elise, False)
        self.seqs.append(self.seq3)

        self.seq4 = NoteSequencer(self.sched, self.synth, 1, (0,88), magic_flute, False)
        self.seqs.append(self.seq4)
    
    def play(self, index):
        self.seqs[index].start()

    # needed to update audio
    def on_update(self):
        self.audio.on_update()


# Displays all game elements: attack boxes, notemon sprites
class GameDisplay(InstructionGroup):
    def __init__(self):
        super(GameDisplay, self).__init__()

        #attack boxes
        self.boxes = []

        self.box0 = AttackDisplay(0, "Winter", 10, True)
        self.boxes.append(self.box0)
        self.add(self.box0)

        self.box1 = AttackDisplay(1, "5th Symphony", 40, True)
        self.boxes.append(self.box1)
        self.add(self.box1)

        self.box2 = AttackDisplay(2, "Fur Elise", 20, True)
        self.boxes.append(self.box2)
        self.add(self.box2)

        self.box3 = AttackDisplay(3, "Magic Flute", 30, True)
        self.boxes.append(self.box3)
        self.add(self.box3)

        self.current_box = 0
        self.boxes[self.current_box].select()

        #notemon sprites
        self.notemon_us = NotemonDisplay(100, False)
        self.notemon_opponent = NotemonDisplay(100, True)

        self.add(self.notemon_us)
        self.add(self.notemon_opponent)

        #battle log
        self.color = Color(1, 1, 1)
        self.add(self.color)

        self.label_x = Window.width // 2
        self.label_y = (1 - 9 * y_margin) * Window.height
        self.text = "You encountered red circle!"
        self.label = CLabelRect(cpos = (self.label_x, self.label_y), text = self.text)
        
        self.add(self.label)
    
    def on_button_up(self):
        if self.current_box == 2 or self.current_box == 3:
            self.boxes[self.current_box].unselect()
            self.current_box -= 2
            self.boxes[self.current_box].select()
    
    def on_button_down(self):
        if self.current_box == 0 or self.current_box == 1:
            self.boxes[self.current_box].unselect()
            self.current_box += 2
            self.boxes[self.current_box].select()
    
    def on_button_left(self):
        if self.current_box == 1 or self.current_box == 3:
            self.boxes[self.current_box].unselect()
            self.current_box -= 1
            self.boxes[self.current_box].select()
    
    def on_button_right(self):
        if self.current_box == 0 or self.current_box == 2:
            self.boxes[self.current_box].unselect()
            self.current_box += 1
            self.boxes[self.current_box].select()
    
    def attack_opponent(self, index):
        damage = self.boxes[index].damage
        self.notemon_opponent.take_damage(damage)

        self.remove(self.label)
        self.text = "You used " + self.boxes[index].name + "!\n"
        self.text += "It dealt " + str(damage) + " damage!\n"

        if self.notemon_opponent.fainted:
            self.text += "Opponent notemon fainted! You win :)"

        self.label = CLabelRect(cpos = (self.label_x, self.label_y), text = self.text)
        self.add(self.label)
    
    def lose_health(self, index):
        damage = self.boxes[index].damage
        self.notemon_us.take_damage(damage)

        self.remove(self.label)
        self.text = "The opponent used " + self.boxes[index].name + "!\n"
        self.text += "It dealt " + str(damage) + " damage!\n"

        if self.notemon_us.fainted:
            self.text += "Your notemon fainted! You lose :("

        self.label = CLabelRect(cpos = (self.label_x, self.label_y), text = self.text)
        self.add(self.label)
    
    def check_complete(self):
        return (self.notemon_opponent.fainted or self.notemon_us.fainted)
    
    def on_update(self):
        self.notemon_opponent.on_update()
        self.notemon_us.on_update()


# Handles game logic.
# Controls the GameDisplay and AudioCtrl based on what happens
class Player(object):
    def __init__(self, audio_ctrl, display):
        super(Player, self).__init__()

        self.audio_ctrl = audio_ctrl
        self.display = display

        self.our_turn = True
        self.complete = False

    # called by MainWidget
    def on_button_down(self):
        self.display.on_button_down()
        
    # called by MainWidget
    def on_button_up(self):
        self.display.on_button_up()
    
    # called by MainWidget
    def on_button_left(self):
        self.display.on_button_left()
    
    # called by MainWidget
    def on_button_right(self):
        self.display.on_button_right()
    
    # called by MainWidget
    def on_button_enter(self):
        if not self.complete: 
            #make sure battle is not over
            if self.our_turn:
                current_box = self.display.current_box
                self.audio_ctrl.play(current_box)
                self.display.attack_opponent(current_box)
                self.our_turn = False
            else:
                opponent_box = random.randint(0, 3)
                self.audio_ctrl.play(opponent_box)
                self.display.lose_health(opponent_box)
                self.our_turn = True
            
            self.complete = self.display.check_complete()

    def on_update(self):
        self.audio_ctrl.on_update()
        self.display.on_update()


if __name__ == "__main__":
    run(MainWidget())
