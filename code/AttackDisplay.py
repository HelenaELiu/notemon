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

x_margin = 1/10 #distance from sides of boxes to edge of screen
y_margin = 1/20 #distance from bottom of boxes to edge of screen
box_width = 7/20 #width of boxes
box_height = 1/6 #height of boxes
y_spacing = 1/20 # y-space between boxes 

# Display for a single attack box
class AttackDisplay(InstructionGroup):
    def __init__(self, attack, index, training=False, y_marg=y_margin):
        super(AttackDisplay, self).__init__()
        self.attack = attack
        self.index = index
        self.training = training
        self.y_margin = y_marg
        self.selected = False

        #opponents attacks are not shown, only ours are
        if training or self.attack.unlocked:
            #graphics
            colors = [0.09, 0, 0.7, 0.85]
            self.color = Color(hsv=(colors[index], 1, 1))
            self.color.a = 0.9
            self.add(self.color)

            w = box_width * Window.width
            h = box_height * Window.height

            x1 = x_margin * Window.width
            y1 = self.y_margin * Window.height + y_spacing * Window.height + h

            x2 = (1 - x_margin) * Window.width - w
            y2 = self.y_margin * Window.height

            if index == 0:
                self.box = Line(rectangle = (x1, y1, w, h), width = 3)
                self.label = CLabelRect(cpos = (x1 + w // 2, y1 + h // 2), text = self.attack.name)
            elif index == 1:
                self.box = Line(rectangle = (x2, y1, w, h), width = 3)
                self.label = CLabelRect(cpos = (x2 + w // 2, y1 + h // 2), text = self.attack.name)
            elif index == 2:
                self.box = Line(rectangle = (x1, y2, w, h), width = 3)
                self.label = CLabelRect(cpos = (x1 + w // 2, y2 + h // 2), text = self.attack.name)
            elif index == 3:
                self.box = Line(rectangle = (x2, y2, w, h), width = 3)
                self.label = CLabelRect(cpos = (x2 + w // 2, y2 + h // 2), text = self.attack.name)

            self.add(self.box)
            self.add(self.label)

    #when considering this box for selection, make outline brighter and larger
    def select(self):
        if self.training or self.attack.unlocked:
            self.color.a = 1
            self.box.width = 10
            self.selected = True

    #revert outline to normal
    def unselect(self):
        if self.training or self.attack.unlocked:
            self.color.a = 0.7
            self.box.width = 3
            self.selected = False

    def on_resize(self, win_size):
        if self.training or self.attack.unlocked:
            self.remove(self.box)
            self.remove(self.label)
            w = box_width * Window.width
            h = box_height * Window.height

            x1 = x_margin * Window.width
            y1 = self.y_margin * Window.height + y_spacing * Window.height + h

            x2 = (1 - x_margin) * Window.width - w
            y2 = self.y_margin * Window.height

            if self.index == 0:
                self.box = Line(rectangle = (x1, y1, w, h), width = 3)
                self.label = CLabelRect(cpos = (x1 + w // 2, y1 + h // 2), font_size=win_size[0]*0.013, text = self.attack.name)
            elif self.index == 1:
                self.box = Line(rectangle = (x2, y1, w, h), width = 3)
                self.label = CLabelRect(cpos = (x2 + w // 2, y1 + h // 2), font_size=win_size[0]*0.013, text = self.attack.name)
            elif self.index == 2:
                self.box = Line(rectangle = (x1, y2, w, h), width = 3)
                self.label = CLabelRect(cpos = (x1 + w // 2, y2 + h // 2), font_size=win_size[0]*0.013, text = self.attack.name)
            elif self.index == 3:
                self.box = Line(rectangle = (x2, y2, w, h), width = 3)
                self.label = CLabelRect(cpos = (x2 + w // 2, y2 + h // 2), font_size=win_size[0]*0.013, text = self.attack.name)

            if self.selected:
                self.select()

            self.add(self.box)
            self.add(self.label)

class AttackBox(InstructionGroup):
    def __init__(self, attacks, training=False, y_marg=y_margin):
        super(AttackBox, self).__init__()
        self.attacks = [AttackDisplay(attack, index, training, y_marg) for (index, attack) in enumerate(attacks)]

        for attack in self.attacks:
            self.add(attack)

    def select(self, ind):
        self.attacks[ind].select()

    def unselect(self, ind):
        self.attacks[ind].unselect()

    def move(self, dir, curr_ind):
        new_ind = curr_ind

        if dir == "up":
            if curr_ind == 2 or curr_ind == 3:
                new_ind = curr_ind - 2
        
        elif dir == "down":
            if curr_ind == 0 or curr_ind == 1:
                new_ind = curr_ind + 2
        
        elif dir == "left":
            if curr_ind == 1 or curr_ind == 3:
                new_ind = curr_ind - 1
        
        elif dir == "right":
            if curr_ind == 0 or curr_ind == 2:
                new_ind = curr_ind + 1

        if self.attacks[new_ind].training or self.attacks[new_ind].attack.unlocked:
            self.attacks[curr_ind].unselect()
            self.attacks[new_ind].select()

        return new_ind
    
    def get_name(self, ind):
        return self.attacks[ind].attack.name

    def get_damage(self, ind):
        return self.attacks[ind].attack.damage

    def on_resize(self, win_size):
        for attack in self.attacks:
            attack.on_resize(win_size)
