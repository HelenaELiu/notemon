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