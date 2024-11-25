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
y_spacing = 1/14 # y-space between boxes

# Display for a single attack box
class NotemonSelection(InstructionGroup):
    def __init__(self, index, name):
        super(NotemonSelection, self).__init__()
        self.index = index
        self.name = name

        #graphics
        colors = [0.1, 0.5, 0.7, 0.85]
        self.color = Color(hsv=(colors[index], 1, 1))
        self.color.a = 0.7
        self.add(self.color)

        w = box_width * Window.width
        h = box_height * Window.height

        x = 1/2 * Window.width - 1/2 * box_width * Window.width
        y = Window.height - ((index + 1) * box_height * Window.height + (index + 1) * y_spacing * Window.height)

        self.box = Line(rectangle = (x, y, w, h), width = 3)
        self.label = CLabelRect(cpos = (x + w // 2, y + h // 2), text = name)
        
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

def box_select(dir, curr_ind):
    if dir == "up":
        return max(curr_ind - 1, 0)
    
    elif dir == "down":
        return min(curr_ind + 1, 3)

    return curr_ind


class TestWidget(BaseWidget):
    def __init__(self):
        super(TestWidget, self).__init__()
        self.selection1 = NotemonSelection(0, "Notemon 1")
        self.selection2 = NotemonSelection(1, "Notemon 2")
        self.selection3 = NotemonSelection(2, "Notemon 3")
        self.selection4 = NotemonSelection(3, "Notemon 4")
        self.canvas.add(self.selection1)
        self.canvas.add(self.selection2)
        self.canvas.add(self.selection3)
        self.canvas.add(self.selection4)

if __name__ == "__main__":
    run(TestWidget())
