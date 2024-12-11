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
from kivy.uix.image import Image
from kivy.uix.widget import Widget 

x_margin = 1/10 #distance from sides of boxes to edge of screens
y_margin = 1/20 #distance from bottom of boxes to edge of screen
box_width = 7/20 #width of boxes
box_height = 1/6 #height of boxes
radius_margin = 1/16 #radius of notemon circles
img_size = (140, 230)

# Display for a single notemon sprite
class NotemonDisplay(InstructionGroup):
    def __init__(self, health, opponent, img_src):
        super(NotemonDisplay, self).__init__()

        #set background color. this can be changed
        Window.clearcolor = (0, 0, 0, 1)

        self.health = health
        self.opponent = opponent
        self.fainted = False

        #graphics
        
        if opponent:
            self.x = (1 - 2 * x_margin) * Window.width
            self.y = (1 - 4 * y_margin) * Window.height
        else:
            self.x = 2 * x_margin * Window.width
            self.y = (1 - 6 * y_margin) * Window.height
        
        self.color = Color(1, 1, 1)
        self.img = Image(source = img_src).texture

        if opponent:
            self.img.flip_horizontal()
        
        self.x -= img_size[0] / 2
        self.y -= img_size[1] / 2

        self.label_x = self.x + img_size[0] / 2
        self.label_y = self.y + img_size[1] * 1.2
        
        self.notemon = Rectangle(texture = self.img, pos = (self.x, self.y), size = img_size)
        self.label = CLabelRect(cpos = (self.label_x, self.label_y), text = "health: " + str(self.health), font_size=0.013*Window.width)

        self.add(self.color)
        self.add(self.notemon)
        self.add(self.label)
    
    def take_damage(self, damage):
        if self.health - damage <= 0:
            self.health = 0
            self.fainted = True
        else:
            self.health -= damage

    def on_resize(self, win_size):
        if self.opponent:
            self.x = (1 - 2 * x_margin) * Window.width
            self.y = (1 - 4 * y_margin) * Window.height
        else:
            self.x = 2 * x_margin * Window.width
            self.y = (1 - 6 * y_margin) * Window.height
        
        img_size = (0.0875*Window.width, 0.19167*Window.height)
        
        self.x -= img_size[0] / 2
        self.y -= img_size[1] / 2

        self.notemon.pos = (self.x, self.y)
        self.notemon.size = img_size
        
        self.label_x = self.x + img_size[0] / 2
        self.label_y = self.y + img_size[1] * 1.2

        self.remove(self.label)
        self.label = CLabelRect(cpos = (self.label_x, self.label_y), text=self.label.text, font_size=0.013*win_size[0])
        self.add(self.label)

    def on_update(self):
        self.remove(self.label)
        self.label = CLabelRect(cpos = (self.label_x, self.label_y), text = "health: " + str(self.health), font_size=0.013*Window.width)
        self.add(self.label)
