from kivy.uix.button import Button
from kivy.graphics import Rectangle

import sys, os
sys.path.insert(0, os.path.abspath('..'))

from imslib.core import BaseWidget, run, lookup
from imslib.audio import Audio
from imslib.mixer import Mixer
from imslib.wavegen import WaveGenerator
from imslib.wavesrc import WaveBuffer, WaveFile
from imslib.noteseq import NoteSequencer
from imslib.screen import Screen

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.window import Window
from imslib.gfxutil import topleft_label, resize_topleft_label, AnimGroup, KFAnim, CEllipse, CLabelRect
from kivy.uix.image import Image

from NotemonDatabase import tot_num

x_margin = 1/10 #distance from sides of boxes to edge of screen
y_margin = 1/20 #distance from bottom of boxes to edge of screen
box_width = 7/20 #width of boxes
y_spacing = 1/20 # y-space between boxes
box_height = (1 - (tot_num - 1) * y_spacing - y_margin * 2) / tot_num #height of boxes
# print(box_height)

class NotemonSelection(InstructionGroup):
    def __init__(self, index, notemon, h=None):
        super(NotemonSelection, self).__init__()
        self.index = index
        self.name = notemon.name
        self.notemon = notemon
        self.selected = False

        if h == None:
            self.color = Color(hsv=(index / tot_num, 1, 1))
        else:
            self.color = Color(hsv=(h, 1, 1))
        self.color.a = 0.7
        self.add(self.color)

        self.box = Rectangle()
        w = box_width * Window.width
        h = box_height * Window.height

        x = 1/2 * Window.width - 1/2 * box_width * Window.width
        y = Window.height * (1 - (index + 1) * box_height - (index) * y_spacing - y_margin)

        self.box = Line(rectangle = (x, y, w, h), width = 3)
        self.label = CLabelRect(cpos = (x + w // 2, y + h // 2), text = self.name)
        self.add(self.box)
        self.add(self.label)

    def on_resize(self, win_size, beginning):
        if self.notemon.unlocked or beginning:
            w = box_width * win_size[0]
            h = box_height * win_size[1]
            x = win_size[0] / 2 - w / 2
            y = win_size[1] / 2 - h / 2
            self.box.pos = (x, y)
            self.box.size = (w, h)
            self.label.cpos = (x + w / 2, y + h / 2)
            
class NotemonSelectionBox(Screen):
    def __init__(self, name):
        super(NotemonSelectionBox, self).__init__(name)
        self.index = 0
        self.selection = None
        self.beginning = True

        self.background = Image(
            source='selection.png',
            allow_stretch=True,
            keep_ratio=False
        )
        self.background.size = Window.size
        self.background.size_hint = (None, None)
        self.background.pos = (0, 0)
        self.add_widget(self.background)

        self.left_arrow = Button(text='<', size_hint=(None, None), size=(50, 50))
        self.right_arrow = Button(text='>', size_hint=(None, None), size=(50, 50))
        self.left_arrow.bind(on_release=self.previous_notemon)
        self.right_arrow.bind(on_release=self.next_notemon)
        self.add_widget(self.left_arrow)
        self.add_widget(self.right_arrow)

        self.select_button = Button(text='Select', size_hint=(None, None), size=(100, 50))
        self.select_button.bind(on_release=self.select_notemon)
        self.add_widget(self.select_button)

    def on_enter(self):
        if self.beginning:
            self.selection = [NotemonSelection(i, self.globals.database[i], self.globals.database[i].h) for i in range(tot_num)]
        else:
            self.selection = [NotemonSelection(i, self.globals.database[i], self.globals.database[i].h) for i in range(tot_num) if self.globals.database[i].unlocked]
        
        self.show_current_notemon()

    def show_current_notemon(self):
        self.canvas.clear()
        self.canvas.add(self.background.canvas)
        self.selection[self.index].select(self.beginning)
        self.canvas.add(self.selection[self.index])

    def previous_notemon(self, instance):
        self.index = max(0, self.index - 1)
        self.show_current_notemon()

    def next_notemon(self, instance):
        self.index = min(len(self.selection) - 1, self.index + 1)
        self.show_current_notemon()

    def select_notemon(self, instance):
        self.globals.pokemon_index = self.selection[self.index].index
        if self.beginning:
            self.globals.database[self.index].unlocked = True
        self.switch_to("main")

    def on_resize(self, win_size):
        self.background.size = win_size
        if self.selection:
            for s in self.selection:
                s.on_resize(win_size, self.beginning)
        
        center_x = win_size[0] / 2
        center_y = win_size[1] / 2
        self.left_arrow.pos = (center_x - 150, center_y)
        self.right_arrow.pos = (center_x + 100, center_y)
        self.select_button.pos = (center_x - 50, center_y - 100)