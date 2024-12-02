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

tot_num = 6

x_margin = 1/10 #distance from sides of boxes to edge of screen
y_margin = 1/20 #distance from bottom of boxes to edge of screen
box_width = 7/20 #width of boxes
y_spacing = 1/20 # y-space between boxes
box_height = (1 - (tot_num - 1) * y_spacing - y_margin * 2) / tot_num #height of boxes
# print(box_height)

# Display for a single attack box
class NotemonSelection(InstructionGroup):
    def __init__(self, index, name, h=None):
        super(NotemonSelection, self).__init__()
        self.index = index
        self.name = name

        #graphics
        # colors = [0.1, 00.5, 0.7, 0.85]
        # self.color = Color(hsv=(colors[index], 1, 1))
        if h == None:
            self.color = Color(hsv=(index / tot_num, 1, 1))
        else:
            self.color = Color(hsv=(h, 1, 1))
        self.color.a = 0.7
        self.add(self.color)

        w = box_width * Window.width
        h = box_height * Window.height

        x = 1/2 * Window.width - 1/2 * box_width * Window.width
        y = Window.height * (1 - (index + 1) * box_height - (index) * y_spacing - y_margin)

        self.box = Line(rectangle = (x, y, w, h), width = 3)
        self.label = CLabelRect(cpos = (x + w // 2, y + h // 2), text = name)
        
        self.add(self.box)
        self.add(self.label)
        self.show = True

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

def box_select(dir, curr_ind):
    if dir == "up":
        return max(curr_ind - 1, 0)
    
    elif dir == "down":
        return min(curr_ind + 1, tot_num - 1)

    return curr_ind


class NotemonSelectionBox(Screen):
    def __init__(self, name):
        super(NotemonSelectionBox, self).__init__(name)
        self.index = 0
        self.selection = None

    def on_enter(self):
        if self.selection is None:
            self.selection = [NotemonSelection(i, self.globals.database[i].name, self.globals.database[i].h) for i in range(tot_num)]
            self.selection[self.index].select()

        for s in self.selection:
            self.canvas.add(s)

    def on_exit(self):
        for s in self.selection:
            self.canvas.remove(s)


    def on_key_down(self, keycode, modifiers):
        if keycode[1] == "enter":
            self.globals.pokemon_index = self.index
            self.switch_to("main")
        
        ind = box_select(keycode[1], self.index)
        if ind != None:
            self.selection[self.index].unselect()
            self.index = ind
            self.selection[self.index].select()



# if __name__ == "__main__":
#     run(TestWidget())
